import base64
import logging
import random
import string
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from locust import HttpUser, task


def generate_random_string(length: int, prefix: str = None):
    letters_and_digits = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters_and_digits) for _ in range(length))
    if prefix:
        return prefix + random_string
    else:
        return random_string


def generate_preds(length: int = None):
    length = random.randint(1, 3) if not length else length
    _preds = []
    # Uncomment below if you want to use simple string for image_frame, will use less memory
    # image_frame = "frame"
    image_frame = get_base64_encoded_image(Path("test_img.jpg"))
    for _ in range(length):
        pred = {
            "image_frame": image_frame,
            "prob": round(random.uniform(0.1, 1.0), 2),
            "tags": []
        }
        _preds.append(pred)
    return _preds


def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


class Tester(HttpUser):
    """Only applicable when using locust"""

    @task
    def send_payload(self):
        payload = {
            "device_id": generate_random_string(4),
            "client_id": generate_random_string(4),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "data": {
                "license_id": generate_random_string(5, "license_"),
                "preds": generate_preds(),
            }
        }
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.client.post("/api", json=payload, headers=headers)


def start_test():
    url = "http://0.0.0.0/api"

    sum_preds = 0
    for i in range(1000):
        preds = generate_preds()
        payload = {
            "device_id": generate_random_string(4),
            "client_id": generate_random_string(4),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "data": {
                "license_id": generate_random_string(5, "license_"),
                "preds": preds,
            }
        }
        logging.info(f"Request #{i}: Number of preds = {len(preds)}")
        sum_preds += len(preds)
        requests.post(url=url, json=payload)

    logging.info(f"Total preds: {sum_preds}")


if __name__ == "__main__":
    ch = logging.StreamHandler(sys.stdout)
    # Change level to [10, 20, 30, 40, 50] for different severity,
    # where 10 is lowest (debug) and 50 is highest (critical)
    logging.basicConfig(
        level=20,
        format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[ch]
    )
    logging.info(f"Starting test script...")

    start = time.perf_counter()
    start_test()
    end = time.perf_counter()
    logging.info(f"Time taken: {end - start} seconds")

    logging.info("Job's done")
