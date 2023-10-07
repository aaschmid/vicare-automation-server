import re
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.health import ROUTE_PREFIX_HEALTH, HealthModel
from app.main import app

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
    assert not checks.session_available
    assert not checks.trust_env


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_checks_positive(dependency_mocker):
    dependency_mocker.oauth_manager.oauth_session.token.is_expired = Mock(return_value=False)
    dependency_mocker.oauth_manager.oauth_session.session = Mock()
    dependency_mocker.oauth_manager.oauth_session.trust_env = True

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    checks = res.checks
    assert checks.auth_token == "valid"
    assert checks.session_available
    assert checks.trust_env


@pytest.mark.parametrize("dependency_mocker", [(app)], indirect=True)
def test_health_checks_for_expired(dependency_mocker):
    dependency_mocker.oauth_manager.oauth_session.token = Mock(return_value=True)

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    checks = res.checks
    assert checks.auth_token == "expired"


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_health_viessmann_api_checks_negative(dependency_mocker):
    dependency_mocker.oauth_manager.oauth_session.get = Mock(return_value=SimpleNamespace(status_code=404))
    dependency_mocker.installations = []

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    api_checks = res.checks.viessmann_api

    assert not api_checks.online
    assert re.fullmatch(r"0:00:(\d\d).(\d+)", api_checks.response_time_in_s)
    assert not api_checks.installations_found


@pytest.mark.parametrize("dependency_mocker", [(app)], indirect=True)
def test_health_viessmann_api_checks(dependency_mocker):
    dependency_mocker.oauth_manager.oauth_session.get = Mock(return_value=SimpleNamespace(status_code=200))
    dependency_mocker.installations = [Mock()]

    response = client.get(ROUTE_PREFIX_HEALTH)

    assert response.status_code == 200

    res = HealthModel(**response.json())
    api_checks = res.checks.viessmann_api

    assert api_checks.online
    assert re.fullmatch(r"0:00:(\d\d).(\d+)", api_checks.response_time_in_s)
    assert api_checks.installations_found
