from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig

from app.api.ventilation import ROUTE_PREFIX_VENTILATION
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_ventilation_should_return_meta_information_on_root(dependency_mocker):
    dependency_mocker.devices = [
        PyViCareDeviceConfig(
            Mock(roles=["type:ventilation"], accessor=Mock(serial="test_serial")), 1234, "test_device", "online"
        )
    ]

    response = client.get(ROUTE_PREFIX_VENTILATION)

    assert response.status_code == 200
    assert response.json() == {
        "deviceId": 1234,
        "model": "test_device",
        "serial": "test_serial",
        "status": "online",
    }


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_ventilation_mode(dependency_mocker):
    dependency_mocker.devices = [
        Mock(
            service=Mock(roles=["type:ventilation"]),
            asVentilation=lambda: Mock(getActiveMode=lambda: "permanent"),
        )
    ]
    response = client.get(f"{ROUTE_PREFIX_VENTILATION}/mode")

    assert response.status_code == 200
    assert response.json() == "permanent"


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_ventilation_program(dependency_mocker):
    dependency_mocker.devices = [
        Mock(
            service=Mock(roles=["type:ventilation"]),
            asVentilation=lambda: Mock(getActiveProgram=lambda: "levelThree"),
        )
    ]
    response = client.get(f"{ROUTE_PREFIX_VENTILATION}/program")

    assert response.status_code == 200
    assert response.json() == "levelThree"
