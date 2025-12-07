import org.apache.spark.SparkConf
import org.apache.spark.streaming._
import org.apache.spark.streaming.kafka010._
import org.apache.spark.streaming.kafka010.LocationStrategies.PreferConsistent
import org.apache.spark.streaming.kafka010.ConsumerStrategies.Subscribe
import org.apache.hadoop.hbase.{HBaseConfiguration, TableName}
import org.apache.hadoop.hbase.client.{ConnectionFactory, Put}
import org.apache.hadoop.hbase.util.Bytes
import com.fasterxml.jackson.databind.ObjectMapper
import java.util.Properties
import java.io.FileInputStream
import scala.collection.JavaConverters._
import org.apache.kafka.clients.consumer.ConsumerRecord

object CarParkHBaseIngestion {

  val HBASE_TABLE = "ayaachi_parking_availability_latest"
  val KAFKA_TOPIC = "ayaachi_car_park"

  def main(args: Array[String]): Unit = {
    if (args.length < 1) {
      System.err.println("Usage: spark-submit ... <path-to-consumer.properties>")
      System.exit(1)
    }

    val propertiesFile = args(0)

    // 1. Load Properties from File
    val javaProps = new Properties()
    val input = new FileInputStream(propertiesFile)
    try {
      javaProps.load(input)
    } finally {
      input.close()
    }

    javaProps.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")
    javaProps.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")

    val kafkaParams = javaProps.asScala.map { case (k, v) => (k, v.asInstanceOf[Object]) }.toMap

    val conf = new SparkConf().setAppName("CarParkHBaseIngestion")
    val ssc = new StreamingContext(conf, Seconds(5))
    ssc.sparkContext.setLogLevel("WARN")

    val topics = Array(KAFKA_TOPIC)
    val stream = KafkaUtils.createDirectStream[String, String](
      ssc, PreferConsistent, Subscribe[String, String](topics, kafkaParams)
    )

    stream.foreachRDD { rdd =>
      val recordsCount = rdd.count()
      if (recordsCount > 0) {
        println(s"\n--- Processing new batch with $recordsCount records ---")

        rdd.foreachPartition { iter =>

          val hbaseConf = HBaseConfiguration.create()
          val connection = ConnectionFactory.createConnection(hbaseConf)
          val table = connection.getTable(TableName.valueOf(HBASE_TABLE))
          val mapper = new ObjectMapper()

          var successCount = 0 // Counter for successful inserts in this partition

          try {
            iter.foreach { record: ConsumerRecord[String, String] =>
              var systemCode = "N/A"
              try {
                val json = mapper.readTree(record.value())

                systemCode = json.get("system_code_number").asText()
                val capacity = json.get("capacity").asInt()
                val occupancy = json.get("occupancy").asInt()
                val queueLength = json.get("queue_length").asInt()
                val trafficCondition = json.get("traffic_condition_nearby").asText()
                val latitude = json.get("latitude").asDouble()
                val longitude = json.get("longitude").asDouble()

                // Calculation: Capacity - Occupancy - QueueLength
                val availableOccupancy = capacity - occupancy - queueLength

                // HBASE PUT
                val rowKey = Bytes.toBytes(systemCode)
                val put = new Put(rowKey)
                val family = Bytes.toBytes("data")

                put.addColumn(family, Bytes.toBytes("capacity"), Bytes.toBytes(capacity.toString))
                put.addColumn(family, Bytes.toBytes("occupancy"), Bytes.toBytes(occupancy.toString))
                put.addColumn(family, Bytes.toBytes("available_occupancy"), Bytes.toBytes(availableOccupancy.toString))
                put.addColumn(family, Bytes.toBytes("queue_length"), Bytes.toBytes(queueLength.toString))
                put.addColumn(family, Bytes.toBytes("traffic_condition"), Bytes.toBytes(trafficCondition))
                put.addColumn(family, Bytes.toBytes("latitude"), Bytes.toBytes(latitude.toString))
                put.addColumn(family, Bytes.toBytes("longitude"), Bytes.toBytes(longitude.toString))

                table.put(put)
                successCount += 1

              } catch {
                case e: Exception =>
                  // Logs parsing or calculation failure for specific record
                  System.err.println(s"ERROR processing record for Lot $systemCode: ${e.getMessage}")
              }
            }
          } finally {
            // Logs batch summary for the partition
            println(s"INFO: Partition processing finished. Successful inserts: $successCount")

            // Close resources within the partition loop
            table.close()
            connection.close()
          }
        }
      } else {
        println("--- Empty batch received. Waiting... ---")
      }
    }

    ssc.start()
    ssc.awaitTermination()
  }
}