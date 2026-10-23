import json
import logging

from confluent_kafka import Consumer, KafkaException
from logging_config import setup_logging
from streaming.producer import KAFKA_CONFIG

logger = logging.getLogger(__name__)

KAFKA_CONFIG = {
    # Same Kafka broker your producer uses.
    "bootstrap.servers": "localhost:9092",

    # Kafka consumers belong to consumer groups.
    "group.id": "mbta-vehicle-consumer",

    # If this consumer group has never read this topic before, start at the oldest available message.
    "auto.offset.reset": "earliest",

    # Explicitly control when Kafka considers a vehicle successfully processed.
    "enable.auto.commit": False
}

TOPIC = "mbta-vehicles"

def consume_vehicles():

    # Creates consumer
    consumer = Consumer(KAFKA_CONFIG)
    # Means: Listen for messages from mbta-vehicles.
    consumer.subscribe([TOPIC])

    logger.info(
        "Subscribed to Kafka topic: %s",
        TOPIC
    )

    try:
        while True:
            # poll() -> "Kafka, do you have another vehicle for me?"
            message = consumer.poll(timeout=1.0)

            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())

            try:
                vehicle = json.loads(
                    message.value().decode("utf-8")
                )

            except json.JSONDecodeError as error:
                logger.error(
                    "Failed to decode Kafka message: %s",
                    error
                )
                continue

            logger.info(
                "Received vehicle %s from Kafka.",
                vehicle.get("id", "unknown")
            )

            # Commit the offset
            consumer.commit(
                message=message,
                asynchronous=False
            )
            # An offset is essentially Kafka's position number for a message within a partition.

            logger.info(
                "Committed Kafka offset %d for partition %d.",
                message.offset(),
                message.partition()
            )

    except KeyboardInterrupt:
        logger.info(
            "Kafka consumer stopped by user."
        )

    except KafkaException:
        logger.info(
            "Kafka consumer encountered an error."
        )

    finally:
        logger.info(
            "Closing Kafka consumer."
        )

        consumer.close()

if __name__ == "__main__":
    setup_logging()
    consume_vehicles()