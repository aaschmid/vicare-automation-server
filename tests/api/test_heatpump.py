from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig

from app.api.heatpump import ROUTE_PREFIX_HEATPUMP
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_should_return_meta_information_on_root(dependency_mocker):
    dependency_mocker.devices = [
        PyViCareDeviceConfig(
            Mock(roles=["type:heatpump"], accessor=Mock(serial="test_serial")), 1234, "test_device", "online"
        )
    ]

    response = client.get(ROUTE_PREFIX_HEATPUMP)

    assert response.status_code == 200
    assert response.json() == {
        "deviceId": 1234,
        "model": "test_device",
        "serial": "test_serial",
        "status": "online",
    }


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_temperature(dependency_mocker):
    dependency_mocker.devices = [
        Mock(
            service=Mock(roles=["type:heatpump"]),
            asHeatPump=lambda: Mock(getOutsideTemperature=lambda: 3.3, getReturnTemperature=lambda: 4.4),
        )
    ]
    response = client.get(f"{ROUTE_PREFIX_HEATPUMP}/temperature")

    assert response.status_code == 200

    assert response.json() == {
        "outside": 3.3,
        "return": 4.4,
    }
