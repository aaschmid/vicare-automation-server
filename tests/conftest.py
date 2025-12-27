from collections import namedtuple
from typing import Dict, Sequence, Tuple, Union
from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import SubRequest
from fastapi import FastAPI
from PyViCare import PyViCare

from app.dependencies import get_request_tracker, get_settings, get_vicare
from app.request_tracking import RequestTracker


def check_args(args) -> (FastAPI, Dict):
    assert type(args) is FastAPI or (
        len(args) > 0 and type(args[0]) is FastAPI
    ), "First or only argument of `dependency_mocker` must be `app: FastAPI`"

    setting_values = {}
    if type(args) is FastAPI:
        app = args

    else:
        app = args[0]
        if len(args) > 1:
            assert isinstance(args[1], dict)
            setting_values = args[1]

    return app, setting_values


@pytest.fixture
def dependency_mocker(request: SubRequest) -> MagicMock:
    app, setting_values = check_args(request.param)

    settings = {
        "email": "test@example.com",
        "password": "password",
        "client_id": "test_client",
        "loxone_url": "http://127.0.0.1",
        "loxone_user": "user",
        "loxone_password": "password",
        **setting_values,
    }
    app.dependency_overrides[get_settings] = lambda: namedtuple("Settings", settings.keys())(*settings.values())

    vicare: PyViCare = MagicMock()
    app.dependency_overrides[get_vicare] = lambda: vicare

    return vicare


@pytest.fixture
def request_tracker() -> RequestTracker:
    """Fixture that provides a reset request tracker for testing."""
    tracker = get_request_tracker()
    tracker.reset()
    return tracker


def record_requests(
    tracker: RequestTracker,
    requests: Sequence[Union[Tuple[str, int], Tuple[str, int, str | None]]],
) -> None:
    """Helper function to record multiple requests in a readable way.

    Args:
        tracker: The RequestTracker instance to record to
        requests: List of request tuples. Each tuple can be:
            - (endpoint, status_code) for successful requests
            - (endpoint, status_code, message) for failed requests with messages

    Example:
        record_requests(tracker, [
            ("/endpoint1", 200),
            ("/endpoint1", 201),
            ("/endpoint2", 404, "Not found"),
            ("/endpoint2", 500, "Server error"),
        ])
    """
    for request_tuple in requests:
        if len(request_tuple) == 2:
            endpoint, status_code = request_tuple
            tracker.record_request(endpoint, status_code, None)
        else:
            endpoint, status_code, message = request_tuple
            tracker.record_request(endpoint, status_code, message)
