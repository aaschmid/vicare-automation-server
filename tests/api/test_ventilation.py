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
    property_map = {
        "device.messages.errors.raw": {"properties": {"entries": {"value": ["error 1", "error 2"]}}},
        "device.productIdentification": {"properties": {"product": {"value": "pId1"}}},
        "ventilation.operating.modes.filterChange": {"properties": {"active": {"value": False}}},
        "ventilation.operating.programs.levelOne": {
            "properties": {"active": {"value": False}, "volumeFlow": {"value": 10, "unit": "m³/h"}}
        },
        "ventilation.operating.programs.levelTwo": {
            "properties": {"active": {"value": True}, "volumeFlow": {"value": 20, "unit": "m³/h"}}
        },
        "ventilation.operating.programs.levelThree": {
            "properties": {"active": {"value": False}, "volumeFlow": {"value": 30, "unit": "m³/h"}}
        },
        "ventilation.operating.programs.levelFour": {
            "properties": {"active": {"value": False}, "volumeFlow": {"value": 40, "unit": "m³/h"}}
        },
    }
    dependency_mocker.devices = [
        PyViCareDeviceConfig(
            Mock(
                roles=["type:ventilation"], accessor=Mock(serial="test_serial"), getProperty=lambda p: property_map[p]
            ),
            1234,
            "test_device",
            "online",
        )
    ]

    response = client.get(ROUTE_PREFIX_VENTILATION)

    assert response.status_code == 200
    assert response.json() == {
        "active": 1,
        "device": {
            "deviceId": 1234,
            "model": "test_device",
            "productIdentification": "pId1",
            "serial": "test_serial",
        },
        "errors": ["error 1", "error 2"],
        "errorCount": 2,
        "filterChange": False,
        "levels": {
            "four": {"active": False, "volumeFlow": "40 m³/h"},
            "one": {"active": False, "volumeFlow": "10 m³/h"},
            "three": {"active": False, "volumeFlow": "30 m³/h"},
            "two": {"active": True, "volumeFlow": "20 m³/h"},
        },
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
