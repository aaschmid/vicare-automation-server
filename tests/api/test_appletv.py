from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.api.appletv import ROUTE_PREFIX_APPLETV
from app.appletv import SystemStatus
from app.main import app

client = TestClient(app)


def _set_status(appletv_mock, system_status: SystemStatus | None) -> None:
    appletv_mock.system_status = AsyncMock(return_value=system_status)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_awake_is_active(dependency_mocker):
    _set_status(dependency_mocker.appletv, SystemStatus.Awake)

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "awake"
        assert data["active"] == 1
        assert data["idle"] == 0
        assert data["screensaver"] == 0
        assert data["atv"]["status"] == "connected"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_screensaver_is_active(dependency_mocker):
    _set_status(dependency_mocker.appletv, SystemStatus.Screensaver)

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "screensaver"
        assert data["active"] == 1
        assert data["screensaver"] == 1
        assert data["idle"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_asleep_is_inactive(dependency_mocker):
    _set_status(dependency_mocker.appletv, SystemStatus.Asleep)

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "asleep"
        assert data["active"] == 0
        assert data["idle"] == 0
        assert data["screensaver"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_idle_is_active(dependency_mocker):
    _set_status(dependency_mocker.appletv, SystemStatus.Idle)

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "idle"
        assert data["active"] == 1
        assert data["idle"] == 1
        assert data["screensaver"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_unknown_is_inactive(dependency_mocker):
    _set_status(dependency_mocker.appletv, SystemStatus.Unknown)

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "unknown"
        assert data["active"] == 0
        assert data["idle"] == 0
        assert data["screensaver"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_unavailable(dependency_mocker):
    _set_status(dependency_mocker.appletv, None)

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    finally:
        app.dependency_overrides.clear()
