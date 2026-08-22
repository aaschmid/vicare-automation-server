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
        "device.productIdentification": {"properties": {"product": {"value": "pId1"}}},
        "ventilation.operating.modes.filterChange": {"properties": {"active": {"value": False}}},
        "ventilation.bypass": {"properties": {"active": {"value": True}}},
        "ventilation.bypass.position": {"properties": {"value": {"value": 3, "unit": "percent"}}},
        "ventilation.filter.runtime": {
            "properties": {
                "operatingHours": {"value": 480, "unit": "hours"},
                "overdueHours": {"value": 0, "unit": "hours"},
                "remainingHours": {"value": 8302, "unit": "hours"},
            }
        },
        "ventilation.filter.pollution.blocked": {"properties": {"value": {"value": 8, "unit": "percent"}}},
        "ventilation.fan.supply": {
            "properties": {
                "current": {"value": 1368, "unit": "rpm"},
                "target": {"value": 0, "unit": "rpm"},
            }
        },
        "ventilation.fan.exhaust": {
            "properties": {
                "current": {"value": 1415, "unit": "rpm"},
                "target": {"value": 0, "unit": "rpm"},
            }
        },
        "ventilation.heatExchanger.frostprotection": {"properties": {"status": {"value": "off"}}},
        "ventilation.heating.recovery": {"properties": {"value": {"value": 100, "unit": "percent"}}},
        "ventilation.sensors.temperature.outside": {"properties": {"value": {"value": 28.1, "unit": "celsius"}}},
        "ventilation.sensors.temperature.supply": {"properties": {"value": {"value": 25.2, "unit": "celsius"}}},
        "ventilation.sensors.temperature.exhaust": {"properties": {"value": {"value": 27.7, "unit": "celsius"}}},
        "ventilation.sensors.temperature.extract": {"properties": {"value": {"value": 24.1, "unit": "celsius"}}},
        "ventilation.sensors.humidity.outdoor": {"properties": {"value": {"value": 26, "unit": "percent"}}},
        "ventilation.sensors.humidity.supply": {"properties": {"value": {"value": 43, "unit": "percent"}}},
        "ventilation.sensors.humidity.exhaust": {"properties": {"value": {"value": 31, "unit": "percent"}}},
        "ventilation.sensors.humidity.extract": {"properties": {"value": {"value": 47, "unit": "percent"}}},
        "ventilation.volumeFlow.current.input": {"properties": {"value": {"value": 127, "unit": "cubicMeter/hour"}}},
        "ventilation.volumeFlow.current.output": {"properties": {"value": {"value": 126, "unit": "cubicMeter/hour"}}},
        "ventilation.operating.modes.active": {
            "commands": {"setMode": {"params": {"mode": {"constraints": {"enum": ["permanent", "sensorDriven"]}}}}},
            "properties": {"value": {"value": "permanent"}},
        },
        "ventilation.operating.modes.permanent": {
            "commands": {
                "setLevel": {
                    "params": {"level": {"constraints": {"enum": ["levelOne", "levelTwo", "levelThree", "levelFour"]}}}
                }
            },
            "properties": {"active": {"value": True}},
        },
        "ventilation.operating.modes.sensorDriven": {
            "properties": {"active": {"value": False}},
        },
        "ventilation.operating.state": {"properties": {"level": {"value": "levelTwo"}}},
        "ventilation.levels.levelOne": {"properties": {"volumeFlow": {"value": 10, "unit": "m³/h"}}},
        "ventilation.levels.levelTwo": {"properties": {"volumeFlow": {"value": 20, "unit": "m³/h"}}},
        "ventilation.levels.levelThree": {"properties": {"volumeFlow": {"value": 30, "unit": "m³/h"}}},
        "ventilation.levels.levelFour": {"properties": {"volumeFlow": {"value": 40, "unit": "m³/h"}}},
    }
    dependency_mocker.vicare.devices = [
        PyViCareDeviceConfig(
            Mock(serial="test_serial", device_id=1234),
            Mock(roles=["type:ventilation"], getProperty=lambda accessor, p: property_map[p]),
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
        "bypass": {"active": 1, "positionPercent": 3},
        "fans": {
            "supply": {"currentRpm": 1368, "targetRpm": 0},
            "exhaust": {"currentRpm": 1415, "targetRpm": 0},
        },
        "filter": {
            "changeModeActive": 0,
            "operatingDays": 20,
            "pollutionPercent": 8,
            "overdueHours": 0,
            "remainingDays": 346,
        },
        "heatExchanger": {"frostProtectionActive": 0, "recoveryPercent": 100},
        "levels": {
            "active": "two",
            "activeNo": 2,
            "four": {"active": 0, "volumeFlow": "40 m³/h"},
            "one": {"active": 0, "volumeFlow": "10 m³/h"},
            "three": {"active": 0, "volumeFlow": "30 m³/h"},
            "two": {"active": 1, "volumeFlow": "20 m³/h"},
        },
        "modes": {
            "permanent": {"active": 1},
            "sensorDriven": {"active": 0},
        },
        "sensors": {
            "temperature": {
                "outsideCelsius": 28.1,
                "supplyCelsius": 25.2,
                "exhaustCelsius": 27.7,
                "extractCelsius": 24.1,
            },
            "humidity": {
                "outdoorPercent": 26,
                "supplyPercent": 43,
                "exhaustPercent": 31,
                "extractPercent": 47,
            },
        },
        "status": "online",
        "volumeFlow": {
            "inputCubicMetersPerHour": 127,
            "outputCubicMetersPerHour": 126,
        },
    }


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_ventilation_mode(dependency_mocker):
    dependency_mocker.vicare.devices = [
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
    dependency_mocker.vicare.devices = [
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
        (app, -1, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (app, 101, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
    indirect=["dependency_mocker"],
)
def test_ventilation_set_mode_permanent_failure(dependency_mocker, level: int, expected: str):
    dependency_mocker.vicare.devices = [
        Mock(
            service=Mock(roles=["type:ventilation"]),
            asVentilation=lambda: Mock(),
        )
    ]
    response = client.put(f"{ROUTE_PREFIX_VENTILATION}/mode/permanent/{level}")

    assert response.status_code == expected


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_ventilation_program(dependency_mocker):
    dependency_mocker.vicare.devices = [
        Mock(
            service=Mock(roles=["type:ventilation"]),
            asVentilation=lambda: Mock(getActiveProgram=lambda: "levelThree"),
        )
    ]
    response = client.get(f"{ROUTE_PREFIX_VENTILATION}/program")

    assert response.status_code == 200
    assert response.json() == "levelThree"
