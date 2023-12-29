from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig
from starlette import status

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


@pytest.mark.parametrize(
    "dependency_mocker, level, expected",
    [
        (app, 0, "levelOne"),
        (app, 22, "levelOne"),
        (app, 44, "levelTwo"),
        (app, 66, "levelThree"),
        (app, 88, "levelFour"),
        (app, 100, "levelFour"),
    ],
    indirect=["dependency_mocker"],
)
def test_ventilation_set_mode_permanent(dependency_mocker, level: int, expected: str):
    setter_mock = Mock()
    dependency_mocker.devices = [
        Mock(
            service=Mock(roles=["type:ventilation"]),
            asVentilation=lambda: Mock(setPermanentLevel=setter_mock),
        )
    ]
    response = client.put(f"{ROUTE_PREFIX_VENTILATION}/mode/permanent/{level}")

    assert response.status_code == 204
    setter_mock.assert_called_once_with(expected)


@pytest.mark.parametrize(
    "dependency_mocker, level, expected",
    [
        (app, -1, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, 101, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
    indirect=["dependency_mocker"],
)
def test_ventilation_set_mode_permanent_failure(dependency_mocker, level: int, expected: str):
    dependency_mocker.devices = [
        Mock(
            service=Mock(roles=["type:ventilation"]),
            asVentilation=lambda: Mock(),
        )
    ]
    response = client.put(f"{ROUTE_PREFIX_VENTILATION}/mode/permanent/{level}")

    assert response.status_code == expected


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
