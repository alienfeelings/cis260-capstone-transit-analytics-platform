import json
import logging

from confluent_kafka import Producer


logger = logging.getLogger(__name__)


KAFKA_CONFIG = {
    "bootstrap.servers": "127.0.0.1:9092"
}

TOPIC_VEHICLES = "mbta-vehicles"
TOPIC_PREDICTIONS = "mbta-predictions"
TOPIC_ALERTS = "mbta-alerts"


producer = Producer(KAFKA_CONFIG)


def delivery_report(error, message):

    if error is not None:
        logger.error(
            "Kafka message delivery failed: %s",
            error
        )
        return

    logger.info(
        "Kafka message delivered to topic %s, partition %d.",
        message.topic(),
        message.partition()
    )


def send_record(
        topic,
        record_type,
        record,
        collected_at
):

    message = json.dumps(
        {
            "collected_at": collected_at.isoformat(),
            record_type: record
        }
    )

    logger.info(
        "Sending %s %s to Kafka topic %s.",
        record_type,
        record.get("id", "unknown"),
        topic
    )

    producer.produce(
        topic=topic,
        value=message.encode("utf-8"),
        callback=delivery_report
    )

    producer.poll(0)


def send_vehicle(
        vehicle,
        collected_at
):

    send_record(
        TOPIC_VEHICLES,
        "vehicle",
        vehicle,
        collected_at
    )

def send_prediction(
        prediction,
        collected_at
):

    send_record(
        TOPIC_PREDICTIONS,
        "prediction",
        prediction,
        collected_at
    )

def send_alert(
        alert,
        collected_at
):

    send_record(
        TOPIC_ALERTS,
        "alert",
        alert,
        collected_at
    )


def flush_producer():

    logger.info(
        "Flushing remaining Kafka messages."
    )

    remaining_messages = producer.flush(
        timeout=10
    )

    if remaining_messages == 0:

        logger.info(
            "Kafka producer flush completed successfully."
        )

    else:
        logger.warning(
            "%d Kafka message(s) were not delivered before timeout.",
            remaining_messages
        )

    return remaining_messages