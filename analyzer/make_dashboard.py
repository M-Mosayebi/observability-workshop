import json
import os

DS = {"type": "prometheus", "uid": "prom"}

PANELS = [
    ("Requests per second",
     "sum(rate(http_requests_total[1m])) by (endpoint)"),
    ("Error ratio",
     'sum(rate(http_requests_total{status="500"}[1m])) / sum(rate(http_requests_total[1m]))'),
    ("Average latency (s)",
     "sum(rate(http_request_duration_seconds_sum[1m])) by (endpoint) / "
     "sum(rate(http_request_duration_seconds_count[1m])) by (endpoint)"),
    ("p95 latency (s)",
     "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le, endpoint))"),
]


def build():
    panels = []
    for i, (title, expr) in enumerate(PANELS):
        panels.append({
            "id": i + 1,
            "type": "timeseries",
            "title": title,
            "datasource": DS,
            "gridPos": {"x": (i % 2) * 12, "y": (i // 2) * 8, "w": 12, "h": 8},
            "targets": [{"expr": expr, "datasource": DS, "refId": "A"}],
        })
    return {
        "uid": "shop-auto",
        "title": "Shop Dashboard (auto-generated)",
        "time": {"from": "now-15m", "to": "now"},
        "refresh": "5s",
        "schemaVersion": 39,
        "panels": panels,
    }


if __name__ == "__main__":
    os.makedirs("grafana/dashboards", exist_ok=True)
    with open("grafana/dashboards/shop.json", "w") as f:
        json.dump(build(), f, indent=2)
    print("Saved grafana/dashboards/shop.json")
