import pytest
from fastapi.testclient import TestClient
from pyatv.const import PowerState

from app.api.appletv import ROUTE_PREFIX_APPLETV
from app.dependencies import get_appletv
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_active(dependency_mocker):
    dependency_mocker.appletv.power.power_state = PowerState.On

    response = client.get(ROUTE_PREFIX_APPLETV)

    assert response.status_code == 200
    assert response.json() == {"active": 1}


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_appletv_inactive(dependency_mocker):
    dependency_mocker.appletv.power.power_state = PowerState.Off

    response = client.get(ROUTE_PREFIX_APPLETV)

    assert response.status_code == 200
    assert response.json() == {"active": 0}


def test_appletv_unavailable():
    app.dependency_overrides[get_appletv] = lambda: None

    response = client.get(ROUTE_PREFIX_APPLETV)

    assert response.status_code == 200
    assert response.json() == {"active": -1}
