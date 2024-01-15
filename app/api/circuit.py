import enum
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from PyViCare import PyViCareHeatPump
from PyViCare.PyViCareHeatingDevice import HeatingCircuit
from starlette import status

from app.api.heating import ROUTE_PREFIX_HEATING
from app.api.heatpump import get_single_heatpump
from app.api.types import HeatingCommand

ROUTE_PREFIX_HEATING_CIRCUIT = f"{ROUTE_PREFIX_HEATING}/circuit"
router = APIRouter(prefix=ROUTE_PREFIX_HEATING_CIRCUIT)


class HeatingCircuitMode(enum.Enum):
    Dhw = "dhw"
    DhwAndHeating = "dhwAndHeating"
    Standby = "standby"


class HeatingCircuitProgram(enum.Enum):
    Comfort = "comfort"
    Default = "default"  # deactivates all manually settable i.e. returns implicitly to default (= timetable based)
    Eco = "eco"
    Normal = "normal"
    Reduced = "reduced"

    @property
    def manually_settable(self):
        return self in [self.Comfort, self.Eco, self.Default]

    @property
    def temperature_settable(self):
        return self in [self.Comfort, self.Normal, self.Reduced]


def get_single_circuit(heatpump: PyViCareHeatPump = Depends(get_single_heatpump)) -> HeatingCircuit:
    result = [c for c in heatpump.circuits]
    if len(result) <= 0:
        raise HTTPException(422, "No circuit device found.")
    if len(result) > 1:
        raise HTTPException(422, "Multiple circuits found, currently unsupported.")
    return result[0]


@router.get("/mode")
def get_mode(circuit: HeatingCircuit = Depends(get_single_circuit)) -> str:
    return circuit.getActiveMode()


@router.put("/mode/{mode}", status_code=status.HTTP_204_NO_CONTENT)
def set_mode(
    mode: Annotated[HeatingCircuitMode, Path(title="The heating circuit mode")],
    circuit: HeatingCircuit = Depends(get_single_circuit),
):
    circuit.setMode(mode.value)


@router.get("/program")
def get_program(circuit: HeatingCircuit = Depends(get_single_circuit)) -> str:
    return circuit.getActiveProgram()


@router.put("/program/{program}", status_code=status.HTTP_204_NO_CONTENT)
def set_program(
    command: Annotated[HeatingCommand, Body()],
    program: Annotated[HeatingCircuitProgram, Path(title="The heating circuit program")],
    # program: Annotated[HeatingCircuitProgram, Path(title="The heating circuit program"), PlainSerializer(lambda x: parse_program(x), HeatingCircuitProgram)],
    circuit: HeatingCircuit = Depends(get_single_circuit),
):
    if not program.manually_settable:
        raise HTTPException(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Can only activate {[p for p in HeatingCircuitProgram if p.manually_settable]} manually.",
        )

    if command == HeatingCommand.Deactivate:
        if program == HeatingCircuitProgram.Default:
            raise HTTPException(
                status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Can only activate Dummy value 'Default', but not deactivate.",
            )
        else:
            circuit.deactivateProgram(program.value)
    elif command == HeatingCommand.Activate:
        if program == HeatingCircuitProgram.Default:
            for p in HeatingCircuitProgram:
                if p.manually_settable and p != program:
                    circuit.deactivateProgram(p.value)
        else:
            circuit.activateProgram(program.value)


@router.put("/program/{program}/{temperature}", status_code=status.HTTP_204_NO_CONTENT)
def set_program_temperature(
    program: Annotated[HeatingCircuitProgram, Path(title="The heating circuit program")],
    temperature: Annotated[int, Path(title="The temperature of the provided heating circuit program", ge=10, le=30)],
    circuit: HeatingCircuit = Depends(get_single_circuit),
):
    if not program.temperature_settable:
        raise HTTPException(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Can only set temperature of {[p for p in HeatingCircuitProgram if p.temperature_settable]} manually.",
        )
    circuit.setProgramTemperature(program.value, temperature)
