import pytest
from fastapi.testclient import TestClient
from pyatv.const import PowerState
from starlette import status

from app.api.appletv import ROUTE_PREFIX_APPLETV
from app.dependencies import PORT_START, get_appletv_connection
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_active(dependency_mocker):
    mock_atv = dependency_mocker.appletv_connection
    mock_atv.power.power_state = PowerState.On

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == 200
        data = response.json()
        assert data["active"] == 1
        assert data["atv"]["port"] == PORT_START + 1
        assert data["atv"]["status"] == "connected"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_inactive(dependency_mocker):
    mock_atv = dependency_mocker.appletv_connection
    mock_atv.power.power_state = PowerState.Off

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == 200
        data = response.json()
        assert data["active"] == 0
        assert data["atv"]["port"] == PORT_START + 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_unavailable(dependency_mocker):
    app.dependency_overrides[get_appletv_connection] = lambda: None

    try:
        response = client.get(ROUTE_PREFIX_APPLETV)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    finally:
        app.dependency_overrides.clear()
