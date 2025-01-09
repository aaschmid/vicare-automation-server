from typing import Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.api.dhw import ROUTE_PREFIX_HEATING_DHW, HeatingDomesticHotWaterLevel
from app.api.types import HeatingCommand
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heating_dhw_get_should_return_current_status(dependency_mocker):
    configure_mocked_heating(
        dependency_mocker,
        Mock(
            getDomesticHotWaterChargingActive=lambda: False,
            getDomesticHotWaterConfiguredTemperature=lambda: 40,
            getDomesticHotWaterMaxTemperature=lambda: 60,
            getDomesticHotWaterMinTemperature=lambda: 10,
            getDomesticHotWaterConfiguredTemperature2=lambda: 45,
            getOneTimeCharge=lambda: False,
            getDomesticHotWaterCirculationPumpActive=lambda: True,
            getDomesticHotWaterCirculationMode=lambda: "10/25-cycle",
            getDomesticHotWaterActive=lambda: True,
            getDomesticHotWaterStorageTemperature=lambda: 40.5,
        ),
    )

    response = client.get(ROUTE_PREFIX_HEATING_DHW)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "active": 1,
        "chargingActive": 0,
        "levels": {
            "main": 40,
            "min": 10,
            "max": 60,
            "temp2": 45,
        },
        "oneTimeCharge": 0,
        "pumps": {
            "circulationActive": 1,
            "mode": "10/25-cycle",
        },
        "storageTemperature": 40.5,
    }


@pytest.mark.parametrize(
    "dependency_mocker, command, expected",
    [
        (app, None, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, "unknown", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
    indirect=["dependency_mocker"],
)
def test_heating_dhw_set_one_time_charge_should_handle_errors_correctly(dependency_mocker, command: str, expected: int):
    heating = configure_mocked_heating(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_DHW}/onetimecharge", json=command)

    assert response.status_code == expected
    heating.assert_not_called()
    heating.activateOneTimeCharge.assert_not_called()
    heating.deactivateOneTimeCharge.assert_not_called()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heating_dhw_one_time_change_should_forward_activation_call_correctly(dependency_mocker):
    heating = configure_mocked_heating(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_DHW}/onetimecharge", json=HeatingCommand.Activate.value)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    heating.assert_not_called()
    heating.activateOneTimeCharge.assert_called_once()
    heating.deactivateOneTimeCharge.assert_not_called()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heating_dhw_one_time_change_should_forward_deactivation_call_correctly(dependency_mocker):
    heating = configure_mocked_heating(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_DHW}/onetimecharge", json=HeatingCommand.Deactivate.value)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    heating.assert_not_called()
    heating.activateOneTimeCharge.assert_not_called()
    heating.deactivateOneTimeCharge.assert_called_once()


@pytest.mark.parametrize(
    "dependency_mocker, level, temperature, expected",
    [
        (app, "unknown", 23, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, HeatingDomesticHotWaterLevel.Temp2.name, -1, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, HeatingDomesticHotWaterLevel.Main.name, 9, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, HeatingDomesticHotWaterLevel.Temp2.name, 31, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
    indirect=["dependency_mocker"],
)
def test_heating_dhw_set_level_temperature_should_handle_errors_correctly(
    dependency_mocker, level: str, temperature: Any, expected: int
):
    heating = configure_mocked_heating(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_DHW}/level/{level}/{temperature}")

    assert response.status_code == expected
    heating.assert_not_called()
    heating.setDomesticHotWaterTemperature.assert_not_called()
    heating.setDomesticHotWaterTemperature2.assert_not_called()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heating_dhw_set_level_main_temperature(dependency_mocker):
    heating = configure_mocked_heating(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_DHW}/level/{HeatingDomesticHotWaterLevel.Main.value}/{30}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    heating.assert_not_called()
    heating.setDomesticHotWaterTemperature.assert_called_once_with(30)
    heating.setDomesticHotWaterTemperature2.assert_not_called()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heating_dhw_set_level_temp2_temperature(dependency_mocker):
    heating = configure_mocked_heating(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_DHW}/level/{HeatingDomesticHotWaterLevel.Temp2.value}/{20}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    heating.assert_not_called()
    heating.setDomesticHotWaterTemperature.assert_not_called()
    heating.setDomesticHotWaterTemperature2.assert_called_once_with(20)


def configure_mocked_heating(dependency_mocker, preconfigured_heating_mock: Mock) -> Mock:
    dependency_mocker.devices = [
        Mock(
            service=Mock(roles=["type:heatpump"]),
            asGeneric=lambda: preconfigured_heating_mock,
        )
    ]
    return preconfigured_heating_mock
