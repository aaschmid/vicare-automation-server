from typing import Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from app.api.heatpump_circuit import (
    ROUTE_PREFIX_HEATPUMP_CIRCUIT,
    HeatingCircuitMode,
    HeatingCircuitProgram,
    HeatingCircuitProgramCommand,
)
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_circuit_get_mode_should_return_current_mode(dependency_mocker):
    mode = HeatingCircuitMode.DhwAndHeating.value
    configure_mocked_circuit(dependency_mocker, Mock(getActiveMode=lambda: mode))

    response = client.get(f"{ROUTE_PREFIX_HEATPUMP_CIRCUIT}/mode")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mode


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_circuit_set_mode_should_forward_call_correctly(dependency_mocker):
    mode = HeatingCircuitMode.Dhw.value
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATPUMP_CIRCUIT}/mode/{mode}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    circuit.setMode.assert_called_once_with(mode)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_heatpump_circuit_get_program_should_return_current_program(dependency_mocker):
    program = HeatingCircuitProgram.Normal.name
    configure_mocked_circuit(dependency_mocker, Mock(getActiveProgram=lambda: program))

    response = client.get(f"{ROUTE_PREFIX_HEATPUMP_CIRCUIT}/program")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == program


@pytest.mark.parametrize(
    "dependency_mocker, program, command, expected",
    [
        (app, "unknown", HeatingCircuitProgramCommand.Activate.value, status.HTTP_404_NOT_FOUND),
        (
            app,
            HeatingCircuitProgram.Normal.name,
            HeatingCircuitProgramCommand.Deactivate.value,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ),
        (app, HeatingCircuitProgram.Default.name, None, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, HeatingCircuitProgram.Default.name, "unknown", status.HTTP_422_UNPROCESSABLE_ENTITY),
        (
            app,
            HeatingCircuitProgram.Default.name,
            HeatingCircuitProgramCommand.Deactivate.value,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ),
    ],
    indirect=["dependency_mocker"],
)
def test_heatpump_circuit_set_program_should_handle_errors_correctly(
    dependency_mocker, program: str, command: str, expected: int
):
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATPUMP_CIRCUIT}/program/{program}", json=command)

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
            HeatingCircuitProgramCommand.Activate,
            [HeatingCircuitProgram.Eco],
            [],
        ),
        (
            app,
            HeatingCircuitProgram.Comfort,
            HeatingCircuitProgramCommand.Deactivate,
            [],
            [HeatingCircuitProgram.Comfort],
        ),
        (
            app,
            HeatingCircuitProgram.Default,
            HeatingCircuitProgramCommand.Activate,
            [],
            [HeatingCircuitProgram.Comfort, HeatingCircuitProgram.Eco],
        ),
    ],
    indirect=["dependency_mocker"],
)
def test_heatpump_circuit_set_program_should_forward_call_correctly(
    dependency_mocker,
    program: HeatingCircuitProgram,
    command: HeatingCircuitProgramCommand,
    expected_activations: list[HeatingCircuitProgram],
    expected_deactivations: list[HeatingCircuitProgram],
):
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATPUMP_CIRCUIT}/program/{program.name}", json=command.value)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    circuit.assert_not_called()
    assert_mock_calls(circuit.activateProgram, [p.name for p in expected_activations])
    assert_mock_calls(circuit.deactivateProgram, [p.name for p in expected_deactivations])


@pytest.mark.parametrize(
    "dependency_mocker, program, temperature, expected",
    [
        (app, "unknown", 23, status.HTTP_404_NOT_FOUND),
        (app, HeatingCircuitProgram.Eco.name, 24, status.HTTP_405_METHOD_NOT_ALLOWED,),
        (app, HeatingCircuitProgram.Comfort.name, -1, status.HTTP_422_UNPROCESSABLE_ENTITY,),
        (app, HeatingCircuitProgram.Normal.name, 9, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (app, HeatingCircuitProgram.Reduced.name, 31, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
    indirect=["dependency_mocker"],
)
def test_heatpump_circuit_set_program_temperature_should_handle_errors_correctly(dependency_mocker, program: str, temperature: Any, expected: int):
    circuit = configure_mocked_circuit(dependency_mocker, Mock())

    response = client.put(f"{ROUTE_PREFIX_HEATPUMP_CIRCUIT}/program/{program}/{temperature}")

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

    response = client.put(f"{ROUTE_PREFIX_HEATPUMP_CIRCUIT}/program/{program.name}/{temperature}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    circuit.assert_not_called()
    circuit.setProgramTemperature.assert_called_once_with(program.name, temperature)


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
