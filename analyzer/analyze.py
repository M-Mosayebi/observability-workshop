import json
from collections import defaultdict

import ollama

LOG_FILE = "logs/app.log"
MODEL = "llama3.2:1b"


# ---------- بخش ۱: خواندن لاگ و آمار هر دقیقه ----------
def load_stats():
    stats = defaultdict(lambda: {"total": 0, "errors": 0, "slow": 0, "reasons": set()})
    with open(LOG_FILE) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            minute = rec["asctime"][:16]  # مثل 2026-11-02 11:55
            s = stats[minute]
            if rec.get("message") == "request_finished":
                s["total"] += 1
                if rec.get("status", 200) >= 500:
                    s["errors"] += 1
                if rec.get("duration_ms", 0) > 1000:
                    s["slow"] += 1
            if rec.get("message") == "payment_failed":
                s["reasons"].add(rec.get("reason", ""))
    return stats


# ---------- بخش ۲: تشخیص anomaly با آمار ساده ----------
def find_anomalies(stats):
    rates = {m: s["errors"] / s["total"] for m, s in stats.items() if s["total"] >= 30}
    if len(rates) < 3:
        return [], 0
    values = sorted(rates.values())
    median = values[len(values) // 2]
    anomalies = []
    for minute, rate in sorted(rates.items()):
        # غیرعادی: بیشتر از 2 برابر میانه و حداقل 30%
        if rate > max(2 * median, 0.12):
            s = stats[minute]
            anomalies.append(
                {
                    "minute": minute,
                    "error_rate": round(rate, 2),
                    "errors": s["errors"],
                    "total": s["total"],
                    "reasons": sorted(s["reasons"]),
                }
            )
    return anomalies, median


# ---------- بخش ۳: تحلیل با AI ----------
def ask_ai(anomalies, median_rate):
    prompt = f"""You are an SRE assistant. Normal error rate is about {median_rate:.0%}.
These minutes were flagged as anomalies (JSON):
{json.dumps(anomalies, indent=2)}

Answer in exactly 3 short sections:
1. SUMMARY: what happened (2 sentences).
2. ROOT CAUSE: most likely cause based on the reasons field.
3. ALERT RULE: one Prometheus alert rule in YAML for high error rate on http_requests_total (label status="500").
"""
    resp = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return resp["message"]["content"]


if __name__ == "__main__":
    stats = load_stats()
    print(f"Minutes analysed: {len(stats)}")

    anomalies, median_rate = find_anomalies(stats)
    if not anomalies:
        print("No anomalies found.")
        raise SystemExit

    print("\n=== Anomalies (found by code) ===")
    for a in anomalies:
        print(a)

    print("\n=== AI analysis (please wait, may take 1-2 min) ===")
    print(ask_ai(anomalies, median_rate))

    # ---------- Alert rule معتبر (ساخته‌شده توسط کد) ----------
    threshold = 0.15
    rule = f"""groups:
  - name: shop-alerts
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{{status="500"}}[1m])) / sum(rate(http_requests_total[1m])) > {threshold}
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Error rate above {threshold:.0%} for 2 minutes"
"""
    with open("analyzer/alert_rules.yml", "w") as f:
        f.write(rule)
    print("\n=== Validated alert rule saved to analyzer/alert_rules.yml ===")
    print(rule)
