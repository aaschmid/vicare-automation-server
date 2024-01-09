import enum
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from PyViCare import PyViCareHeatPump
from PyViCare.PyViCareHeatingDevice import HeatingCircuit
from starlette import status

from app.api.heatpump import ROUTE_PREFIX_HEATPUMP, get_single_heatpump
from app.api.types import HeatingCommand

ROUTE_PREFIX_HEATPUMP_CIRCUIT = f"{ROUTE_PREFIX_HEATPUMP}/circuit"
router = APIRouter(prefix=ROUTE_PREFIX_HEATPUMP_CIRCUIT)


class HeatingCircuitMode(enum.Enum):
    Dhw = "dhw"
    DhwAndHeating = "dhwAndHeating"
    Standby = "standby"


class HeatingCircuitProgram(enum.Enum):
    Comfort = ("comfort", True, True)
    Default = (
        "default",
        True,
        False,
    )  # deactivates all manually settable i.e. returns implicitly to default (= timetable based)
    Eco = ("eco", True, False)
    Normal = ("normal", False, True)
    Reduced = ("reduced", False, True)

    @property
    def name(self):
        return self.value[0]

    @property
    def manually_settable(self):
        return self.value[1]

    @property
    def temperature_settable(self):
        return self.value[2]


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
    program: Annotated[str, Path(title="The heating circuit program")],
    # program: Annotated[HeatingCircuitProgram, Path(title="The heating circuit program"), PlainSerializer(lambda x: parse_program(x), HeatingCircuitProgram)],
    circuit: HeatingCircuit = Depends(get_single_circuit),
):
    program_ = _parse_program(program)

    if not program_.manually_settable:
        raise HTTPException(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Can only activate {[p for p in HeatingCircuitProgram if p.manually_settable]} manually.",
        )

    if command == HeatingCommand.Deactivate:
        if program_ == HeatingCircuitProgram.Default:
            raise HTTPException(
                status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Can only activate Dummy value 'Default', but not deactivate.",
            )
        else:
            circuit.deactivateProgram(program_.name)
    elif command == HeatingCommand.Activate:
        if program_ == HeatingCircuitProgram.Default:
            for p in HeatingCircuitProgram:
                if p.manually_settable and p != program_:
                    circuit.deactivateProgram(p.name)
        else:
            circuit.activateProgram(program_.name)


@router.put("/program/{program}/{temperature}", status_code=status.HTTP_204_NO_CONTENT)
def set_program_temperature(
    program: Annotated[str, Path(title="The heating circuit program")],
    temperature: Annotated[int, Path(title="The temperature of the provided heating circuit program", ge=10, le=30)],
    circuit: HeatingCircuit = Depends(get_single_circuit),
):
    program_ = _parse_program(program)

    if not program_.temperature_settable:
        raise HTTPException(
            status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Can only set temperature of {[p for p in HeatingCircuitProgram if p.temperature_settable]} manually.",
        )
    circuit.setProgramTemperature(program_.name, temperature)


def _parse_program(program: str) -> HeatingCircuitProgram:
    # Manually parse program as I couldn't find how to let it do FastAPI with enhanced enum
    results = [p for p in HeatingCircuitProgram if p.name == program]
    if len(results) != 1:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Program must be one of {[p.name for p in HeatingCircuitProgram if p.name]} but was {program}.",
        )
    return results[0]
