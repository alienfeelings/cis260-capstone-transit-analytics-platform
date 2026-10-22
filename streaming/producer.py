import json
import logging
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092"
}
TOPIC = "mbta-vehicles"

producer = Producer(KAFKA_CONFIG)

def delivery_report(error, message):

    if error is not None:
        logger.error("Kafka message delivery failed: %s",
                     error
        )
        return
    logger.info(
        "Kafka message delivered to topic %s, partition %d.",
        message.topic(),
        message.partition()
    )

def send_vehicle(vehicle):

    message = json.dumps(vehicle)

    logger.info(
        "Sending vehicle %s to Kafka.",
        vehicle.get("id", "unknown")
    )

    producer.produce(
        topic=TOPIC,
        value=message.encode("utf-8"),
        callback=delivery_report
    )

    producer.poll(0)

def flush_producer():

    logger.info("Flushing remaining Kafka messages.")
    producer.flush()

if __name__ == "__main__":

    test_vehicle = {
        "id": "test-vehicle-1",
        "route_id": "Red",
        "speed": 25
    }
    send_vehicle(test_vehicle)
    flush_producer()
