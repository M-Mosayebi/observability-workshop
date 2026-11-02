import logging
import random
import time

from flask import Flask, jsonify, request
from pythonjsonlogger import jsonlogger

app = Flask(__name__)

# ---------- Structured logging ----------
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
file_handler = logging.FileHandler("logs/app.log")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger("shop")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def log_request(response):
    duration_ms = round((time.time() - request.start_time) * 1000)
    logger.info(
        "request_finished",
        extra={
            "endpoint": request.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


# ---------- Endpoints ----------
@app.route("/")
def home():
    return jsonify(message="Welcome to the shop")


@app.route("/products")
def products():
    time.sleep(random.uniform(0.05, 0.2))
    return jsonify(products=["laptop", "phone", "headphones"])


@app.route("/checkout")
def checkout():
    time.sleep(random.uniform(0.1, 0.3))
    if random.random() < 0.2:  # 20% failure
        logger.error(
            "payment_failed",
            extra={"endpoint": "/checkout", "reason": "payment gateway timeout"},
        )
        return jsonify(error="payment failed"), 500
    return jsonify(message="order placed")


@app.route("/search")
def search():
    if random.random() < 0.3:  # 30% slow
        delay = random.uniform(1, 3)
        logger.warning(
            "slow_search",
            extra={"endpoint": "/search", "delay_s": round(delay, 2)},
        )
        time.sleep(delay)
    else:
        time.sleep(random.uniform(0.05, 0.15))
    return jsonify(results=["item1", "item2"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
