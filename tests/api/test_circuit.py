from typing import Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.api.circuit import (
    ROUTE_PREFIX_HEATING_CIRCUIT,
    HeatingCircuitMode,
    HeatingCircuitProgram,
)
from app.api.types import HeatingCommand
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_circuit_get_mode_should_return_current_mode(dependency_mocker):
    mode = HeatingCircuitMode.DhwAndHeating.value
    configure_mocked_circuit(dependency_mocker, Mock(getActiveMode=lambda: mode))

    response = client.get(f"{ROUTE_PREFIX_HEATING_CIRCUIT}/mode")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mode


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_circuit_set_mode_should_forward_call_correctly(dependency_mocker):
    mode = HeatingCircuitMode.Dhw.value
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_CIRCUIT}/mode/{mode}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    circuit.setMode.assert_called_once_with(mode)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_circuit_get_program_should_return_current_program(dependency_mocker):
    program = HeatingCircuitProgram.Normal.name
    configure_mocked_circuit(dependency_mocker, Mock(getActiveProgram=lambda: program))

    response = client.get(f"{ROUTE_PREFIX_HEATING_CIRCUIT}/program")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == program


@pytest.mark.parametrize(
    "dependency_mocker, program, command, expected",
    [
        (app, "unknown", HeatingCommand.Activate.value, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (
            app,
            HeatingCircuitProgram.Normal.value,
            HeatingCommand.Deactivate.value,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ),
        (app, HeatingCircuitProgram.Default.value, None, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, HeatingCircuitProgram.Default.value, "unknown", status.HTTP_422_UNPROCESSABLE_ENTITY),
        (
            app,
            HeatingCircuitProgram.Default.value,
            HeatingCommand.Deactivate.value,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ),
    ],
    indirect=["dependency_mocker"],
)
def test_heatpump_circuit_set_program_should_handle_errors_correctly(
    dependency_mocker, program: str, command: str, expected: int
):
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_CIRCUIT}/program/{program}", json=command)

    assert response.status_code == expected
    circuit.assert_not_called()
    circuit.activateProgram.assert_not_called()
    circuit.deactivateProgram.assert_not_called()


@pytest.mark.parametrize(
    "dependency_mocker, program, command, expected_activations, expected_deactivations",
    [
        (
            app,
            HeatingCircuitProgram.Eco,
            HeatingCommand.Activate,
            [HeatingCircuitProgram.Eco],
            [],
        ),
        (
            app,
            HeatingCircuitProgram.Comfort,
            HeatingCommand.Deactivate,
            [],
            [HeatingCircuitProgram.Comfort],
        ),
        (
            app,
            HeatingCircuitProgram.Default,
            HeatingCommand.Activate,
            [],
            [HeatingCircuitProgram.Comfort, HeatingCircuitProgram.Eco],
        ),
    ],
    indirect=["dependency_mocker"],
)
def test_heatpump_circuit_set_program_should_forward_call_correctly(
    dependency_mocker,
    program: HeatingCircuitProgram,
    command: HeatingCommand,
    expected_activations: list[HeatingCircuitProgram],
    expected_deactivations: list[HeatingCircuitProgram],
):
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_CIRCUIT}/program/{program.value}", json=command.value)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    circuit.assert_not_called()
    assert_mock_calls(circuit.activateProgram, [p.value for p in expected_activations])
    assert_mock_calls(circuit.deactivateProgram, [p.value for p in expected_deactivations])


@pytest.mark.parametrize(
    "dependency_mocker, program, temperature, expected",
    [
        (app, "unknown", 23, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (
            app,
            HeatingCircuitProgram.Eco.value,
            24,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ),
        (
            app,
            HeatingCircuitProgram.Comfort.value,
            -1,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (app, HeatingCircuitProgram.Normal.value, 9, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, HeatingCircuitProgram.Reduced.value, 31, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
    indirect=["dependency_mocker"],
)
def test_heatpump_circuit_set_program_temperature_should_handle_errors_correctly(
    dependency_mocker, program: str, temperature: Any, expected: int
):
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_CIRCUIT}/program/{program}/{temperature}")

    assert response.status_code == expected
    circuit.assert_not_called()
    circuit.setProgramTemperature.assert_not_called()


@pytest.mark.parametrize(
    "dependency_mocker, program, temperature",
    [
        (app, HeatingCircuitProgram.Comfort, 10),
        (app, HeatingCircuitProgram.Normal, 30),
        (app, HeatingCircuitProgram.Reduced, 20),
    ],
    indirect=["dependency_mocker"],
)
def test_heatpump_circuit_set_program_temperature(dependency_mocker, program: HeatingCircuitProgram, temperature: int):
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATING_CIRCUIT}/program/{program.value}/{temperature}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    circuit.assert_not_called()
    circuit.setProgramTemperature.assert_called_once_with(program.value, temperature)


def configure_mocked_circuit(dependency_mocker, preconfigured_circuit_mock: Mock) -> Mock:
    dependency_mocker.devices = [
        Mock(
            service=Mock(roles=["type:heatpump"]),
            asHeatPump=lambda: Mock(circuits=[preconfigured_circuit_mock]),
        )
    ]
    return preconfigured_circuit_mock


def assert_mock_calls(mock: Mock, expected_call_args: list[str]):
    if len(expected_call_args) == 0:
        mock.assert_not_called()
    else:
        assert mock.call_count == len(expected_call_args)
        for arg in expected_call_args:
            mock.assert_any_call(arg)
