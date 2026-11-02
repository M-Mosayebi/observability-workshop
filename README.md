# Observability Workshop

A small Flask shop with full observability and AI-assisted analysis.

## Stack
- Flask app: structured JSON logs, Prometheus metrics, OpenTelemetry traces
- Prometheus + Grafana + Jaeger (Docker Compose)
- Ollama (llama3.2:1b) for local, free AI analysis

## Run
    docker compose up -d
    python app/main.py        # terminal 1
    python app/traffic.py     # terminal 2
    touch faults/checkout_errors   # inject failure (rm to stop)

## Analysis
    python analyzer/analyze.py         # anomaly detection + AI summary + alert rule
    python analyzer/rootcause.py       # error logs -> Jaeger traces
    python analyzer/make_dashboard.py  # dashboard as code (Grafana provisioning)

## URLs
- Grafana: :3000 | Prometheus: :9090 | Jaeger: :16686
