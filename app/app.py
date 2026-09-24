"""TaskForge: a tiny in-memory to-do list API with Prometheus metrics."""
import itertools
import time

from flask import Flask, Response, g, jsonify, render_template, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Histogram,
                               generate_latest)

app = Flask(__name__)

# --- Metrics (names and labels are part of the demo contract) --------------
REQUESTS = Counter("app_http_requests_total", "Total HTTP requests",
                   ["method", "endpoint", "status"])
LATENCY = Histogram("app_http_request_duration_seconds",
                    "HTTP request latency in seconds", ["endpoint"])
ERRORS = Counter("app_http_errors_total", "Total HTTP 5xx responses",
                 ["endpoint"])


def endpoint_label():
    """Route template (e.g. /api/tasks/<int:task_id>) keeps label cardinality low."""
    return request.url_rule.rule if request.url_rule else "unmatched"


@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record_metrics(response):
    # Don't let Prometheus scraping pollute the numbers.
    if request.path != "/metrics":
        endpoint = endpoint_label()
        REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
        LATENCY.labels(endpoint).observe(time.perf_counter() - g.start)
        if response.status_code >= 500:
            ERRORS.labels(endpoint).inc()
    return response


# --- In-memory storage ------------------------------------------------------
tasks = {}
_ids = itertools.count(1)


def not_found():
    return jsonify(error="task not found"), 404


# --- API --------------------------------------------------------------------
@app.get("/api/tasks")
def list_tasks():
    return jsonify(list(tasks.values()))


@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify(error="title is required"), 400
    task = {"id": next(_ids), "title": title, "done": False}
    tasks[task["id"]] = task
    return jsonify(task), 201


@app.patch("/api/tasks/<int:task_id>")
def complete_task(task_id):
    task = tasks.get(task_id)
    if task is None:
        return not_found()
    task["done"] = True
    return jsonify(task)


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    if tasks.pop(task_id, None) is None:
        return not_found()
    return "", 204


# --- Operational endpoints --------------------------------------------------
@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/error")
def error():
    """Always fails; used to demo alerting."""
    return jsonify(error="intentional failure"), 500


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# --- Web UI (templates/index.html + static/) -------------------------------
@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
