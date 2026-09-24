import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from app import app, tasks  # noqa: E402


@pytest.fixture
def client():
    tasks.clear()
    return app.test_client()


def add(client, title="write tests"):
    return client.post("/api/tasks", json={"title": title})


def test_list_empty(client):
    r = client.get("/api/tasks")
    assert r.status_code == 200 and r.get_json() == []


def test_create_and_list(client):
    r = add(client)
    assert r.status_code == 201
    assert r.get_json()["title"] == "write tests"
    assert len(client.get("/api/tasks").get_json()) == 1


def test_create_requires_title(client):
    assert client.post("/api/tasks", json={"title": "  "}).status_code == 400
    assert client.post("/api/tasks", data="nope").status_code == 400


def test_mark_done(client):
    tid = add(client).get_json()["id"]
    r = client.patch(f"/api/tasks/{tid}")
    assert r.status_code == 200 and r.get_json()["done"] is True


def test_patch_unknown_404(client):
    assert client.patch("/api/tasks/999").status_code == 404


def test_delete(client):
    tid = add(client).get_json()["id"]
    assert client.delete(f"/api/tasks/{tid}").status_code == 204
    assert client.get("/api/tasks").get_json() == []


def test_delete_unknown_404(client):
    assert client.delete("/api/tasks/999").status_code == 404


def test_health(client):
    assert client.get("/health").status_code == 200


def test_error_is_500(client):
    assert client.get("/error").status_code == 500


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200 and b"TaskForge" in r.data


def test_metrics_exposed(client):
    client.get("/health")
    client.get("/error")
    body = client.get("/metrics").get_data(as_text=True)
    assert 'app_http_requests_total{endpoint="/health",method="GET",status="200"}' in body
    assert "app_http_request_duration_seconds_bucket" in body
    assert 'app_http_errors_total{endpoint="/error"}' in body
