from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.heatpump import ROUTE_PREFIX_HEATPUMP
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_should_return_meta_information_on_root(dependency_mocker):
    property_map = {
        "device.messages.errors.raw": {"properties": {"entries": {"value": ["error x"]}}},
    }
    dependency_mocker.devices = [
        Mock(
            asHeatPump=lambda: Mock(
                compressors=[
                    Mock(
                        getActive=lambda: True,
                        getHours=lambda: 100,
                        getPhase=lambda: "?",
                        getStarts=lambda: 12,
                    )
                ],
                getBoilerSerial=lambda: "boiler-serial",
                getBufferMainTemperature=lambda: 21.3,
                getControllerSerial=lambda: "controller-serial",
                getOutsideTemperature=lambda: 3.3,
                getSupplyTemperaturePrimaryCircuit=lambda: 29,
                getSupplyTemperatureSecondaryCircuit=lambda: 24.7,
                getReturnTemperature=lambda: 4.4,
            ),
            device_id=1234,
            device_model="test_device",
            service=Mock(
                roles=["type:heatpump"],
                accessor=Mock(serial="test_serial"),
                getProperty=lambda p: property_map[p],
            ),
            status="online",
        )
    ]

    response = client.get(ROUTE_PREFIX_HEATING_HEATPUMP)

    assert response.status_code == 200
    assert response.json() == {
        "device": {
            "boilerSerial": "boiler-serial",
            "controllerSerial": "controller-serial",
            "deviceId": 1234,
            "model": "test_device",
            "serial": "test_serial",
        },
        "compressor": {
            "active": True,
            "hours": 100,
            "phase": "?",
            "starts": 12,
        },
        "errors": ["error x"],
        "temperature": {
            "buffer": 21.3,
            "outside": 3.3,
            "primaryCircuitSupply": 29,
            "return": 4.4,
            "secondaryCircuitSupply": 24.7,
        },
        "status": "online",
    }
