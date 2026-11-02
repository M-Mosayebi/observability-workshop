import json

import requests

LOG_FILE = "logs/app.log"
JAEGER = "http://localhost:16686"


def last_error_trace_ids(n=3):
    """trace_id آخرین درخواست‌های خطادار را از لاگ می‌گیرد."""
    ids = []
    with open(LOG_FILE) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                rec.get("message") == "request_finished"
                and rec.get("status", 200) >= 500
                and rec.get("trace_id")
            ):
                ids.append(rec["trace_id"])

    return ids[-n:]


def show_trace(trace_id):
    r = requests.get(f"{JAEGER}/api/traces/{trace_id}", timeout=10)
    if r.status_code != 200:
        print(f"  trace {trace_id[:8]}... not found in Jaeger")
        return
    trace = r.json()["data"][0]
    print(f"\nTrace {trace_id}")
    for span in trace["spans"]:
        has_error = any(
            t["key"] == "error" or (t["key"] == "http.status_code" and t["value"] >= 500)
            for t in span["tags"]
        )
        flag = "ERROR" if has_error else "ok"
        print(f"  - {span['operationName']:<30} {span['duration']/1000:>8.1f} ms  [{flag}]")


if __name__ == "__main__":
    ids = last_error_trace_ids()
    if not ids:
        print("No error requests found in logs.")
    for tid in ids:
        show_trace(tid)
    print("\nOpen in browser: http://192.168.162.130:16686/trace/<trace_id>")
