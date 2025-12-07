import org.apache.spark.SparkConf
import org.apache.spark.streaming._
import org.apache.spark.streaming.kafka010._
import org.apache.spark.streaming.kafka010.LocationStrategies.PreferConsistent
import org.apache.spark.streaming.kafka010.ConsumerStrategies.Subscribe
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileSystem, Path}
import com.fasterxml.jackson.databind.ObjectMapper
import java.util.Properties
import java.io.FileInputStream
import java.io.PrintWriter
import scala.collection.JavaConverters._
import scala.collection.mutable.ListBuffer
import org.apache.kafka.clients.consumer.ConsumerRecord

object CarParkHiveIngestion {

  val RAW_HDFS_LOCATION = "hdfs://ip-172-31-91-77.ec2.internal:8020/ayaachi/data/"
  val KAFKA_TOPIC = "ayaachi_car_park"

  def main(args: Array[String]): Unit = {
    if (args.length < 1) {
      System.err.println("Usage: spark-submit ... <path-to-consumer.properties>")
      System.exit(1)
    }

    val propertiesFile = args(0)

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

    val conf = new SparkConf().setAppName("CarParkHiveIngestion")
    val ssc = new StreamingContext(conf, Seconds(30)) // Batch interval: 30 seconds
    ssc.sparkContext.setLogLevel("WARN") // Reduce noise

    val topics = Array(KAFKA_TOPIC)
    val stream = KafkaUtils.createDirectStream[String, String](
      ssc, PreferConsistent, Subscribe[String, String](topics, kafkaParams)
    )

    stream.foreachRDD { rdd =>
      val recordsCount = rdd.count()
      if (recordsCount > 0) {
        println(s"\n--- Batch Start: Processing $recordsCount total records for HDFS write ---")

        // Process each partition and write to HDFS
        rdd.foreachPartition { iter =>

          // HDFS SETUP
          val hadoopConf = new Configuration()
          val hdfsFileSystem = FileSystem.get(hadoopConf)
          val hdfsRecords = new ListBuffer[String]()

          val mapper = new ObjectMapper()
          var recordsProcessedInPartition = 0
          var systemCode = "N/A"

          try {
            iter.foreach { record: ConsumerRecord[String, String] =>
              try {
                val json = mapper.readTree(record.value())

                val id = json.get("id").asText()
                systemCode = json.get("system_code_number").asText() // Track for error logging
                val capacity = json.get("capacity").asText()
                val latitude = json.get("latitude").asText()
                val longitude = json.get("longitude").asText()
                val occupancy = json.get("occupancy").asText()
                val vehicleType = json.get("vehicle_type").asText()
                val trafficCondition = json.get("traffic_condition_nearby").asText()
                val queueLength = json.get("queue_length").asText()
                val isSpecialDay = json.get("is_special_day").asText()
                val lastUpdatedDate = json.get("last_updated_date").asText()
                val lastUpdatedTime = json.get("last_updated_time").asText()

                val csvLine = Seq(
                  id, systemCode, capacity, latitude, longitude, occupancy, vehicleType,
                  trafficCondition, queueLength, isSpecialDay, lastUpdatedDate, lastUpdatedTime
                ).map(_.toString).mkString(",")

                hdfsRecords += csvLine
                recordsProcessedInPartition += 1

              } catch {
                case e: Exception =>
                  System.err.println(s"❌ ERROR: Failed to parse JSON for Lot $systemCode: ${e.getMessage}")
              }
            }

            // Write the collected CSV lines to HDFS (one file per batch/partition)
            if (hdfsRecords.nonEmpty) {
              // Create a unique file name using the current timestamp and partition ID
              val fileName = s"raw_batch_${System.currentTimeMillis()}-${scala.util.Random.nextInt(10000)}.csv"
              val filePath = new Path(RAW_HDFS_LOCATION + fileName)

              val outputStream = hdfsFileSystem.create(filePath, false)
              val writer = new PrintWriter(outputStream)

              try {
                hdfsRecords.foreach(writer.println)

                println(s"SUCCESS: Wrote ${hdfsRecords.size} records to HDFS at $filePath")
              } finally {
                writer.close()
                outputStream.close()
              }
            } else {
              println(s"INFO: Partition processed 0 records.")
            }

          } finally {}
        }
      } else {
        println("--- Empty batch received. Waiting for data... ---")
      }
    }

    ssc.start()
    ssc.awaitTermination()
  }
}