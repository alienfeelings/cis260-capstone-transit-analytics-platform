import json
import os
import logging
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from transformations.vehicles_transform import (
    transform_vehicle,
    load_vehicle_records
)

from confluent_kafka import Consumer, KafkaException
from logging_config import setup_logging
from streaming.producer import KAFKA_CONFIG

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

KAFKA_CONFIG = {
    # Same Kafka broker your producer uses.
    "bootstrap.servers": "127.0.0.1:9092",

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
    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    logger.info(
        "Connected to PostgreSQL for Kafka vehicle ingestion."
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
                # vehicle = json.loads(
                #     message.value().decode("utf-8")
                # )
                payload = json.loads(
                    message.value().decode("utf-8")
                )
                vehicle = payload["vehicle"]
                collected_at = datetime.fromisoformat(
                    payload["collected_at"]
                )

                logger.info(
                    "Received vehicle %s from Kafka.",
                    vehicle.get("id", "unknown")
                )

                transformed_vehicle = transform_vehicle(
                    vehicle,
                    collected_at
                )

                if transformed_vehicle is None:
                    logger.warning(
                        "Vehicle %s could not be transformed.",
                        vehicle.get("id", "unknown")
                    )
                    consumer.commit(
                        message=message,
                        asynchronous=False
                    )
                    continue

            except json.JSONDecodeError as error:
                logger.error(
                    "Failed to decode Kafka message: %s",
                    error
                )
                continue

            try:
                with connection.cursor() as cursor:
                    rows_loaded = load_vehicle_records(
                        cursor,
                        [transformed_vehicle]
                    )
                connection.commit()

                logger.info(
                    "Loaded vehicle %s into PostgreSQL.",
                    transformed_vehicle["vehicle_id"]
                )

            except Exception:
                connection.rollback()

                logger.exception(
                    "Failed to load vehicle %s into PostgreSQL.",
                    vehicle.get("id", "unknown")
                )
                continue

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

        logger.info(
            "Closing PostgreSQL connection."
        )
        connection.close()

if __name__ == "__main__":
    setup_logging()
    consume_vehicles()