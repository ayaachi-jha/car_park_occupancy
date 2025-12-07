import json
import time
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer
from faker import Faker
from typing import Dict


KAFKA_BROKERS = ['boot-public-byg.mpcs53014kafka.2siu49.c2.kafka.us-east-1.amazonaws.com:9196']
KAFKA_TOPIC = 'ayaachi_car_park'
SLEEP_TIME = 5  # Seconds to wait between sending messages
NUM_MESSAGES = 200 # Total messages to send


SECURITY_CONFIG: Dict[str, str] = {
    'security_protocol': 'SASL_SSL',
    'sasl_mechanism': 'SCRAM-SHA-512',
    'sasl_plain_username': 'mpcs53014-2025',
    'sasl_plain_password': 'A3v4rd4@ujjw',
    'request_timeout_ms': 20000,
    'retry_backoff_ms': 500,
}

# Mock data
PARKING_LOTS = {
    "BHMBCCMKT01": {"cap": 577, "lat": 52.4800, "lon": -1.8900},
    "BHMBCCCMB01": {"cap": 300, "lat": 52.4780, "lon": -1.9020},
    "BHMBCCPGG01": {"cap": 800, "lat": 52.4850, "lon": -1.8850},
    "BHMBCCMSQ01": {"cap": 150, "lat": 52.4750, "lon": -1.9100},
    "BHMBCCPARK01": {"cap": 720, "lat": 52.4839, "lon": -1.8943},
    "BHMBCCLANP02": {"cap": 450, "lat": 52.4725, "lon": -1.9077},
    "BHMBCCQTRF03": {"cap": 910, "lat": 52.4951, "lon": -1.8790},
    "BHMBCCLIBX04": {"cap": 215, "lat": 52.4788, "lon": -1.9122},
    "BHMBCCBRD05": {"cap": 630, "lat": 52.4770, "lon": -1.9030}
}

fake = Faker()
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    **SECURITY_CONFIG # Pass security settings
)

def generate_mock_record(lot_id, data, record_id):
    """Generates a single mock parking record with snake_case keys."""

    current_capacity = data['cap']

    # Generate timestamp
    ts = datetime.now() - timedelta(seconds=random.randint(1, 60))
    ts_date_str = ts.strftime("%d-%m-%Y")
    ts_time_str = ts.strftime("%H:%M:%S")

    # Generate operational data
    max_occupancy = int(current_capacity * 0.95)
    occupancy = random.randint(int(current_capacity * 0.1), max_occupancy)
    queue_length = 0
    if occupancy > int(current_capacity * 0.7):
        queue_length = random.randint(1, 5)

    available_occupancy = current_capacity - occupancy - queue_length

    # JSON payload
    record = {
        "id": str(record_id),
        "system_code_number": lot_id,
        "capacity": str(current_capacity),
        "latitude": str(data['lat']),
        "longitude": str(data['lon']),
        "occupancy": str(occupancy),
        "vehicle_type": random.choice(["car", "bike", "truck"]),
        "traffic_condition_nearby": random.choice(["low", "average", "high"]),
        "queue_length": str(queue_length),
        "is_special_day": random.choice(["0", "1"]),
        "last_updated_date": ts_date_str,
        "last_updated_time": ts_time_str
    }

    return record, available_occupancy


record_counter = 0
print(f"Starting producer. Sending {NUM_MESSAGES} messages to {KAFKA_TOPIC}...")

for i in range(NUM_MESSAGES):
    # Cycle through parking lots
    lot_id, data = random.choice(list(PARKING_LOTS.items()))

    record_counter += 1
    mock_data, calculated_avail = generate_mock_record(lot_id, data, record_counter)

    # Send the message
    producer.send(KAFKA_TOPIC, value=mock_data)

    print(f"Sent: {mock_data['system_code_number']} | Calculated Avail: {calculated_avail}")
    print(f"Raw JSON sent: {mock_data}")
    time.sleep(SLEEP_TIME)

producer.flush()
print("Production complete.")