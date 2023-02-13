import csv
import functools
import logging
import os
import pickle
import sys
import threading
from copy import copy
from pathlib import Path

import pika

QUEUE_NAME = os.environ["QUEUENAME"]


def ack_message(channel, delivery_tag):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        channel.basic_ack(delivery_tag)
    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass


def write_to_csv(filename, message: dict, tlock: threading.Lock):
    """Write to a CSV file in a thread-safe manner"""
    tlock.acquire()
    with open(filename, "a", ) as f:
        writer = csv.DictWriter(f, fieldnames=message.keys())
        # Write the headers only when the write pointer is at 0, aka a new file
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(message)
    tlock.release()


def do_work(channel, delivery_tag, body, tlock: threading.Lock):
    """Deserialize the message and write to CSV file."""
    message = pickle.loads(body)

    # The thread ID may get recycled when a thread exits and another is created,
    # so it's not a good indicator of how many threads have been used
    # https://docs.python.org/3/library/threading.html#threading.get_ident
    thread_id = threading.get_ident()

    logging.info(
        f"Active threads: {threading.active_count()} Thread id: {thread_id} Delivery tag: {delivery_tag} Message: {message}")

    data = message.pop("data")
    msg_to_csv = copy(message)
    msg_to_csv["license_id"] = data["license_id"]

    for pred in data["preds"]:
        # Each item in preds should have its own row in the CSV file,
        # so overwrite the same keys for only items in pred
        msg_to_csv["image_frame"] = pred["image_frame"]
        msg_to_csv["prob"] = pred["prob"]
        msg_to_csv["tags"] = pred["tags"]
        write_to_csv(Path("data.csv"), msg_to_csv, tlock)

    cb = functools.partial(ack_message, channel, delivery_tag)
    channel.connection.add_callback_threadsafe(cb)


def callback(channel, method_frame, _header_frame, body, args):
    """The callback function when a new message is received"""
    threads, tlock = args
    delivery_tag = method_frame.delivery_tag

    t = threading.Thread(target=do_work, args=(channel, delivery_tag, body, tlock))
    t.start()
    threads.append(t)


def main():
    rabbit_params = pika.ConnectionParameters(host="rabbitmq")
    tlock = threading.Lock()

    # Use context manager to automatically close the connection when the process stops
    with pika.BlockingConnection(rabbit_params) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)
        channel.basic_qos(prefetch_size=0, prefetch_count=10)

        threads = []
        on_message_callback = functools.partial(callback, args=(threads, tlock))

        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message_callback)
        channel.start_consuming()

    # Wait for all to complete
    # Note: may not be called when container is stopped?
    logging.info(f"Number of threads to join: {len(threads)}")
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    # Init regular logging
    ch = logging.StreamHandler(sys.stdout)
    # Change level to [10, 20, 30, 40, 50] for different severity,
    # where 10 is lowest (debug) and 50 is highest (critical)
    logging.basicConfig(
        level=20,
        format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[ch]
    )
    logging.info(f"Starting consumer...")

    sys.exit(main())
