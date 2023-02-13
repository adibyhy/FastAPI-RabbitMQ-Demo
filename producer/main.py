import logging
import os
import pickle
import sys

import pika
from fastapi import FastAPI

from pyd_models import PayloadModel

QUEUE_NAME = os.environ["QUEUENAME"]

app = FastAPI(title="FastAPI + RabbitMQ + Consumer Demo")
rabbit_params = pika.ConnectionParameters(host="rabbitmq")


@app.on_event("startup")
async def logging_init():
    """Configure logging to output to stdout and format it for easy viewing"""
    ch = logging.StreamHandler(sys.stdout)
    # Change level to [10, 20, 30, 40, 50] for different severity,
    # where 10 is lowest (debug) and 50 is highest (critical)
    logging.basicConfig(
        level=20,
        format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[ch]
    )
    logging.info(f"Starting producer...")


@app.get("/")
def read_root():
    return {"Developer": "Adib Yahaya"}


@app.post("/api")
def accept_payload(payload: PayloadModel):
    for pred in payload.data.preds:
        if pred["prob"] < 0.25:
            pred["tags"].append("low_prob")

    # Convert to dict for easy serialization
    payload_dict = payload.dict()

    logging.debug(f"Payload received: {payload_dict}")

    # Use context manager to automatically close the connection when the process stops
    with pika.BlockingConnection(rabbit_params) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)
        channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=pickle.dumps(payload_dict))

    return {"status": "received"}
