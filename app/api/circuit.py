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

    @classmethod
    def no_of(cls, value: str) -> int:
        return {cls.Standby.value: 0, cls.Dhw.value: 1, cls.DhwAndHeating.value: 2}.get(value, -1)


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

    @classmethod
    def no_of(cls, value: str) -> int:
        return {
            cls.Default.value: 0,
            cls.Eco.value: 1,
            cls.Comfort.value: 2,
            cls.Normal.value: 3,
            cls.Reduced.value: 4,
        }.get(value, -1)


def get_single_circuit(heatpump: PyViCareHeatPump = Depends(get_single_heatpump)) -> HeatingCircuit:
    result = [c for c in heatpump.circuits]
    if len(result) <= 0:
        raise HTTPException(422, "No circuit device found.")
    if len(result) > 1:
        raise HTTPException(422, "Multiple circuits found, currently unsupported.")
    return result[0]


@router.get("")
def get_circuit(circuit: HeatingCircuit = Depends(get_single_circuit)) -> dict:
    no = circuit.circuit
    program = circuit.getActiveProgram()
    programs = {
        program: circuit.service.getProperty(f"heating.circuits.{no}.operating.programs.{program}")["properties"]
        for program in circuit.getPrograms()
    }

    mode = circuit.getActiveMode()
    return {
        "active": 1 if circuit.getActive() else 0,
        "circuitNo": no,
        "frostProtectionActive": 1 if circuit.getFrostProtectionActive() else 0,
        "heatingCurve": {
            "shift": circuit.getHeatingCurveShift(),
            "slope": circuit.getHeatingCurveSlope(),
        },
        "mode": mode,
        "modeNo": HeatingCircuitMode.no_of(mode),
        "name": circuit.getName(),
        "pumpActive": 1 if circuit.getCirculationPumpActive() else 0,
        "programs": {
            "active": program,
            "activeNo": HeatingCircuitProgram.no_of(program),
        }
        | {
            program: {
                "active": 1 if v["active"]["value"] else 0,
                "demand": v["demand"]["value"] if "demand" in v else "n/a",
                "temperature": v["temperature"]["value"] if "temperature" in v else "n/a",
            }
            for program, v in programs.items()
        },
        "temperature": {
            "levels": {
                "min": circuit.getTemperatureLevelsMin(),
                "max": circuit.getTemperatureLevelsMax(),
            },
            "supply": circuit.getSupplyTemperature(),
            "target": circuit.service.getProperty(f"heating.circuits.{no}.temperature")["properties"]["value"]["value"],
            "targetCalc": circuit.getTargetSupplyTemperature(),
        },
    }


@router.put("/mode/{mode}", status_code=status.HTTP_204_NO_CONTENT)
def set_mode(
    mode: Annotated[HeatingCircuitMode, Path(title="The heating circuit mode")],
    circuit: HeatingCircuit = Depends(get_single_circuit),
):
    circuit.setMode(mode.value)


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
