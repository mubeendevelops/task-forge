#!/usr/bin/env python3
"""Send mixed traffic to TaskForge (standard library only).

Usage: python scripts/load_test.py [--url http://localhost:5000] [--duration 60] [--delay 0.05]
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request


def call(base, method, path, body=None):
    """Send one request and return the HTTP status (errors included)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, b""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default="http://localhost:5000")
    p.add_argument("--duration", type=float, default=60, help="seconds")
    p.add_argument("--delay", type=float, default=0.05, help="seconds between requests")
    p.add_argument("--error-rate", type=float, default=0.15,
                   help="fraction of requests that hit /error")
    a = p.parse_args()

    counts = {}
    ids = []
    end = time.time() + a.duration
    while time.time() < end:
        roll = random.random()
        if roll < a.error_rate:
            status, _ = call(a.url, "GET", "/error")
        elif roll < 0.35:
            status, body = call(a.url, "POST", "/api/tasks",
                                {"title": f"task {random.randint(1, 999)}"})
            if status == 201:
                ids.append(json.loads(body)["id"])
        elif roll < 0.60:
            status, _ = call(a.url, "GET", "/api/tasks")
        elif roll < 0.75 and ids:
            status, _ = call(a.url, "PATCH", f"/api/tasks/{random.choice(ids)}")
        elif roll < 0.85 and ids:
            status, _ = call(a.url, "DELETE", f"/api/tasks/{ids.pop()}")
        elif roll < 0.92:
            status, _ = call(a.url, "GET", "/api/tasks/999999")  # 404
        else:
            status, _ = call(a.url, "GET", "/health")
        counts[status] = counts.get(status, 0) + 1
        time.sleep(a.delay)

    print("Done. Responses by status:", dict(sorted(counts.items())))


if __name__ == "__main__":
    main()
