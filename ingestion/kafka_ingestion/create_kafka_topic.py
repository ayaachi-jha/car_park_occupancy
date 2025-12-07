import json
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from typing import Dict

KAFKA_BROKERS = ['boot-public-byg.mpcs53014kafka.2siu49.c2.kafka.us-east-1.amazonaws.com:9196']
TOPIC_NAME = 'ayaachi_car_park'
NUM_PARTITIONS = 3
REPLICATION_FACTOR = 3
SECURITY_CONFIG: Dict[str, str] = {
    'security_protocol': 'SASL_SSL',
    'sasl_mechanism': 'SCRAM-SHA-512',
    'sasl_plain_username': 'mpcs53014-2025',
    'sasl_plain_password': 'A3v4rd4@ujjw',
    'request_timeout_ms': 20000,
    'retry_backoff_ms': 500,
}

def create_kafka_topic():
    """Connects to Kafka using security settings and attempts to create the topic."""

    print(f"Attempting to connect to Kafka brokers: {KAFKA_BROKERS}")

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=KAFKA_BROKERS,
            client_id='topic_creator_client',
            **SECURITY_CONFIG
        )
        print("Successfully connected to Kafka Admin Client.")

        topic_list = [
            NewTopic(
                name=TOPIC_NAME,
                num_partitions=NUM_PARTITIONS,
                replication_factor=REPLICATION_FACTOR,
            )
        ]

        # Create the topic
        print(f"Creating topic '{TOPIC_NAME}' with {NUM_PARTITIONS} partitions...")
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print(f"Topic '{TOPIC_NAME}' created successfully.")

    except TopicAlreadyExistsError:
        print(f"Topic '{TOPIC_NAME}' already exists. Skipping creation.")
    except Exception as e:
        print(f"An error occurred during topic creation:")
        print(f"Error: {e}")
    finally:
        if 'admin_client' in locals():
            admin_client.close()

if __name__ == "__main__":
    create_kafka_topic()