import re
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.api.health import ROUTE_PREFIX_HEALTH, HealthModel
from app.main import app
from tests.conftest import record_requests

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_should_set_no_cache_header(dependency_mocker):
    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "no-cache"


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_status_code(dependency_mocker):
    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_general_result(dependency_mocker):
    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    assert res.status == "UP"
    assert re.search(r"0:00:(\d\d)\.(\d+)", res.uptime)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_checks_negative(dependency_mocker):
    dependency_mocker.oauth_manager.oauth_session.token = None
    dependency_mocker.oauth_manager.oauth_session.session = None
    dependency_mocker.oauth_manager.oauth_session.trust_env = False

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    checks = res.checks
    assert checks.auth_token == "invalid"
    assert checks.no_of_installations == 0
    assert not checks.session_available
    assert not checks.trust_env


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_checks_positive(dependency_mocker):
    dependency_mocker.oauth_manager.oauth_session.token.is_expired = Mock(return_value=False)
    dependency_mocker.oauth_manager.oauth_session.session = Mock()
    dependency_mocker.oauth_manager.oauth_session.trust_env = True
    dependency_mocker.installations = [Mock(), Mock(), Mock()]

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    checks = res.checks
    assert checks.auth_token == "valid"
    assert checks.no_of_installations == 3
    assert checks.session_available
    assert checks.trust_env


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_checks_for_expired(dependency_mocker):
    dependency_mocker.oauth_manager.oauth_session.token = Mock(return_value=True)

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    checks = res.checks
    assert checks.auth_token == "expired"


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_status_code_auth_token_error(dependency_mocker, request_tracker):
    dependency_mocker.oauth_manager.oauth_session.token = None

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200
    res = HealthModel(**response.json())
    assert res.status_code == 2


@pytest.mark.parametrize(
    "dependency_mocker, failure_status, expected_code",
    [
        (app, status.HTTP_200_OK, 1),  # Successful request
        (app, status.HTTP_401_UNAUTHORIZED, 3),  # Authentication Error
        (app, status.HTTP_429_TOO_MANY_REQUESTS, 4),  # Rate Limit Error
        (app, status.HTTP_424_FAILED_DEPENDENCY, 5),  # Invalid Configuration Error
        (app, status.HTTP_405_METHOD_NOT_ALLOWED, 6),  # Not Supported Error
        (app, status.HTTP_500_INTERNAL_SERVER_ERROR, 7),  # Internal Server Error
        (app, status.HTTP_502_BAD_GATEWAY, 8),  # Uncategorized error
    ],
    indirect=["dependency_mocker"],
)
def test_health_status_code_error_mapping(dependency_mocker, failure_status, expected_code, request_tracker):
    dependency_mocker.oauth_manager.oauth_session.token.is_expired = Mock(return_value=False)
    record_requests(request_tracker, [("/test/endpoint", failure_status, "Test error message")])

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200
    res = HealthModel(**response.json())
    assert res.status_code == expected_code


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_request_stats_empty(dependency_mocker, request_tracker):
    # Check health endpoint
    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200
    res = HealthModel(**response.json())

    request_stats = res.requests.request_stats
    assert request_stats["overall"]["failure"] == 0
    assert request_stats["overall"]["success"] == 0
    assert request_stats["by_status_code"] == {}
    assert request_stats["by_endpoint"] == {}


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_includes_request_stats(dependency_mocker, request_tracker):
    record_requests(
        request_tracker,
        [
            ("/test/endpoint", status.HTTP_200_OK),
            ("/test/endpoint", status.HTTP_204_NO_CONTENT),
            ("/test/endpoint1", status.HTTP_204_NO_CONTENT),
            ("/test/endpoint", status.HTTP_401_UNAUTHORIZED, "Unauthorized"),
            ("/test/endpoint", status.HTTP_401_UNAUTHORIZED, "Unauthorized"),
            ("/test/endpoint", status.HTTP_403_FORBIDDEN, "Forbidden"),
            ("/test/endpoint2", status.HTTP_404_NOT_FOUND, "Not found"),
            ("/test/endpoint3", status.HTTP_404_NOT_FOUND, "Not found"),
        ],
    )

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    # Note: JSON serialization converts integer keys to strings, so we check for string keys
    request_stats = HealthModel(**response.json()).requests.request_stats
    assert request_stats["overall"]["success"] == 3
    assert request_stats["overall"]["failure"] == 5
    assert request_stats["by_status_code"] == {
        str(status.HTTP_200_OK): 1,
        str(status.HTTP_204_NO_CONTENT): 2,
        str(status.HTTP_401_UNAUTHORIZED): 2,
        str(status.HTTP_403_FORBIDDEN): 1,
        str(status.HTTP_404_NOT_FOUND): 2,
    }
    assert request_stats["by_endpoint"] == {
        "/test/endpoint": {
            str(status.HTTP_200_OK): 1,
            str(status.HTTP_204_NO_CONTENT): 1,
            str(status.HTTP_401_UNAUTHORIZED): 2,
            str(status.HTTP_403_FORBIDDEN): 1,
        },
        "/test/endpoint1": {
            str(status.HTTP_204_NO_CONTENT): 1,
        },
        "/test/endpoint2": {
            str(status.HTTP_404_NOT_FOUND): 1,
        },
        "/test/endpoint3": {
            str(status.HTTP_404_NOT_FOUND): 1,
        },
    }


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_last_failure_none_when_no_failures(dependency_mocker, request_tracker):
    record_requests(request_tracker, [("/test/endpoint", status.HTTP_200_OK)])

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200
    res = HealthModel(**response.json())
    assert res.requests.last_failure_message is None


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_includes_last_failure(dependency_mocker, request_tracker):
    timestamp = time.time() - 55
    with patch("app.request_tracking.time.time", return_value=timestamp):
        record_requests(
            request_tracker,
            [("/test/endpoint", status.HTTP_401_UNAUTHORIZED, "Authentication failed")],
        )

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    last_failure = HealthModel(**response.json()).requests.last_failure_message
    assert last_failure is not None
    assert last_failure.endpoint == "/test/endpoint"
    assert last_failure.message == "Authentication failed"
    assert last_failure.status_code == status.HTTP_401_UNAUTHORIZED
    assert last_failure.timestamp is not None
    assert last_failure.timestamp == datetime.fromtimestamp(timestamp).isoformat()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_status_code_ignores_expired_failures(dependency_mocker, request_tracker):
    dependency_mocker.oauth_manager.oauth_session.token.is_expired = Mock(return_value=False)
    with patch("app.request_tracking.time.time", return_value=(time.time() - (61 * 60))):
        record_requests(request_tracker, [("/test/endpoint", status.HTTP_500_INTERNAL_SERVER_ERROR, "Server error")])

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200
    res = HealthModel(**response.json())
    assert res.status_code == 1
    assert res.requests.last_failure_message is not None
    assert res.requests.last_failure_message.message == "Server error"
    assert res.requests.last_failure_message.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_endpoint_not_tracked(dependency_mocker, request_tracker):
    client.get(ROUTE_PREFIX_HEALTH)
    client.get(ROUTE_PREFIX_HEALTH)
    client.get(ROUTE_PREFIX_HEALTH)

    stats = request_tracker.get_statistics()

    # Health endpoint should not appear in stats
    assert stats["overall"]["success"] == 0
    assert stats["overall"]["failure"] == 0
    assert stats["by_endpoint"] == {}
    assert stats["by_status_code"] == {}
