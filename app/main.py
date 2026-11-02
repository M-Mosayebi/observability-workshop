from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
import logging
import random
import time

from flask import Flask, jsonify, request
from pythonjsonlogger import jsonlogger

app = Flask(__name__)
# ---------- Metrics (Prometheus) ----------
REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["endpoint", "method", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "Request latency in seconds", ["endpoint"]
)

# ---------- Tracing (OpenTelemetry) ----------
provider = TracerProvider(resource=Resource.create({"service.name": "shop"}))
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
)
trace.set_tracer_provider(provider)
FlaskInstrumentor().instrument_app(app)
tracer = trace.get_tracer("shop")

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
    duration = time.time() - request.start_time
    REQUESTS.labels(request.path, request.method, response.status_code).inc()
    LATENCY.labels(request.path).observe(duration)

    ctx = trace.get_current_span().get_span_context()
    logger.info(
        "request_finished",
        extra={
            "endpoint": request.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": round(duration * 1000),
            "trace_id": format(ctx.trace_id, "032x"),
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
    with tracer.start_as_current_span("search_database"):
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

    
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
