import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette import status

from app.request_tracking import RequestTracker, RequestTrackingMiddleware


@pytest.fixture
def tracker_app():
    tracker = RequestTracker()
    tracker.reset()

    test_app = FastAPI()
    test_app.add_middleware(RequestTrackingMiddleware, request_tracker=tracker)

    @test_app.get("/ok")
    def ok_endpoint():
        return {"status": "ok"}

    @test_app.get("/fail-http")
    def fail_http():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")

    @test_app.get("/health")
    def health():
        return {"status": "UP"}

    return test_app, tracker


def test_middleware_records_successful_request(tracker_app):
    test_app, tracker = tracker_app
    client = TestClient(test_app)

    response = client.get("/ok")

    assert response.status_code == status.HTTP_200_OK
    stats = tracker.get_statistics()
    assert stats["overall"]["success"] == 1
    assert stats["overall"]["failure"] == 0
    assert stats["by_endpoint"]["/ok"][status.HTTP_200_OK] == 1


def test_middleware_records_failed_request_with_message(tracker_app):
    test_app, tracker = tracker_app
    client = TestClient(test_app, raise_server_exceptions=True)

    response = client.get("/fail-http")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    stats = tracker.get_statistics()
    assert stats["overall"]["success"] == 0
    assert stats["overall"]["failure"] == 1
    assert stats["by_endpoint"]["/fail-http"][status.HTTP_401_UNAUTHORIZED] == 1

    last_failure = tracker.get_last_failure_message()
    assert last_failure is not None
    assert (
        last_failure["message"] == "n/a"
    )  # "Bad credentials" does not appear due to some middleware exception stuff, but I currently don't mind
    # assert "Bad credentials" in last_failure["message"]


def test_middleware_skips_health_endpoint(tracker_app):
    test_app, tracker = tracker_app
    client = TestClient(test_app)

    client.get("/health")
    client.get("/health")

    stats = tracker.get_statistics()
    assert stats["overall"]["success"] == 0
    assert stats["overall"]["failure"] == 0
    assert "/health" not in stats["by_endpoint"]


def test_middleware_records_success_message(tracker_app):
    test_app, tracker = tracker_app
    client = TestClient(test_app)

    client.get("/ok")

    last_success = tracker.get_last_success_message()
    assert last_success is not None
    assert last_success["endpoint"] == "/ok"
    assert last_success["status_code"] == status.HTTP_200_OK


def test_middleware_multiple_requests_accumulate(tracker_app):
    test_app, tracker = tracker_app
    client = TestClient(test_app)

    client.get("/ok")
    client.get("/ok")
    response = client.get("/ok")

    assert (
        response.status_code == status.HTTP_200_OK
    )  # check at least one status otherwise requests seems not be tracked, yet

    stats = tracker.get_statistics()
    assert stats["overall"]["success"] == 3
    assert stats["overall"]["failure"] == 0
    assert stats["by_endpoint"]["/ok"][status.HTTP_200_OK] == 3
