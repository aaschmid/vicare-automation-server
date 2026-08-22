from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from PyViCare import PyViCareDeviceConfig, PyViCareVentilationDevice
from PyViCare.PyViCare import PyViCare
from starlette import status

from app import dependencies

ROUTE_PREFIX_VENTILATION = "/ventilation"
router = APIRouter(prefix=ROUTE_PREFIX_VENTILATION)


def get_single_ventilation_device(vicare: PyViCare = Depends(dependencies.get_vicare)) -> PyViCareDeviceConfig:
    result = [d for d in vicare.devices for role in d.service.roles if "type:ventilation" in role]
    if len(result) <= 0:
        raise HTTPException(422, "No ventilation device found.")
    if len(result) > 1:
        raise HTTPException(422, "Multiple ventilation devices found, currently unsupported.")
    return result[0]


def get_single_ventilation(vicare: PyViCare = Depends(dependencies.get_vicare)) -> PyViCareVentilationDevice:
    return get_single_ventilation_device(vicare).asVentilation()


@router.get("")
def get_ventilation(
    device: PyViCareDeviceConfig = Depends(get_single_ventilation_device),
    ventilation: PyViCareVentilationDevice = Depends(get_single_ventilation),
) -> dict:
    def prop(name: str) -> dict:
        return ventilation.getProperty(name)["properties"]

    level_strings = ventilation.getVentilationLevels()
    levels = {level: prop(f"ventilation.levels.{level}") for level in level_strings}

    active_level = ventilation.getVentilationLevel()

    filter_change = prop("ventilation.operating.modes.filterChange")["active"]["value"]
    filter_runtime = prop("ventilation.filter.runtime")

    return {
        "active": 1 if device.status.lower() == "online" else 0,
        "bypass": {
            "active": 1 if prop("ventilation.bypass")["active"]["value"] else 0,
            "positionPercent": prop("ventilation.bypass.position")["value"]["value"],
        },
        "device": {
            "deviceId": device.device_id,
            "model": device.device_model,
            "productIdentification": prop("device.productIdentification")["product"]["value"],
            "serial": device.accessor.serial,
        },
        "fans": {
            "supply": {
                "currentRpm": prop("ventilation.fan.supply")["current"]["value"],
                "targetRpm": prop("ventilation.fan.supply")["target"]["value"],
            },
            "exhaust": {
                "currentRpm": prop("ventilation.fan.exhaust")["current"]["value"],
                "targetRpm": prop("ventilation.fan.exhaust")["target"]["value"],
            },
        },
        "filter": {
            "changeModeActive": 1 if filter_change else 0,
            "operatingDays": round(filter_runtime["operatingHours"]["value"] / 24),
            "pollutionPercent": prop("ventilation.filter.pollution.blocked")["value"]["value"],
            "overdueHours": filter_runtime["overdueHours"]["value"],
            "remainingDays": round(filter_runtime["remainingHours"]["value"] / 24),
        },
        "heatExchanger": {
            "frostProtectionActive": (
                0 if prop("ventilation.heatExchanger.frostprotection")["status"]["value"] == "off" else 1
            ),
            "recoveryPercent": prop("ventilation.heating.recovery")["value"]["value"],
        },
        "levels": {"active": active_level[5:].lower(), "activeNo": level_strings.index(active_level) + 1}
        | {
            # strip off `level` from levels
            level[5:].lower(): {
                "active": 1 if level == active_level else 0,
                "volumeFlow": f"{v['volumeFlow']['value']} {v['volumeFlow']['unit']}",
            }
            for level, v in levels.items()
        },
        "modes": {
            mode: {"active": 1 if ventilation.getVentilationMode(mode) else 0}
            for mode in ventilation.getVentilationModes()
        },
        "sensors": {
            "temperature": {
                "outsideCelsius": prop("ventilation.sensors.temperature.outside")["value"]["value"],
                "supplyCelsius": prop("ventilation.sensors.temperature.supply")["value"]["value"],
                "exhaustCelsius": prop("ventilation.sensors.temperature.exhaust")["value"]["value"],
                "extractCelsius": prop("ventilation.sensors.temperature.extract")["value"]["value"],
            },
            "humidity": {
                "outdoorPercent": prop("ventilation.sensors.humidity.outdoor")["value"]["value"],
                "supplyPercent": prop("ventilation.sensors.humidity.supply")["value"]["value"],
                "exhaustPercent": prop("ventilation.sensors.humidity.exhaust")["value"]["value"],
                "extractPercent": prop("ventilation.sensors.humidity.extract")["value"]["value"],
            },
        },
        "status": device.status,
        "volumeFlow": {
            "inputCubicMetersPerHour": prop("ventilation.volumeFlow.current.input")["value"]["value"],
            "outputCubicMetersPerHour": prop("ventilation.volumeFlow.current.output")["value"]["value"],
        },
    }


@router.get("/mode")
def get_mode(ventilation: PyViCareVentilationDevice = Depends(get_single_ventilation)) -> str:
    return ventilation.getActiveMode()


@router.put("/mode/permanent/{level}", status_code=status.HTTP_204_NO_CONTENT)
def set_mode_permanent(
    level: Annotated[int, Path(title="The ventilation level in percent", ge=0, le=100)],
    ventilation: PyViCareVentilationDevice = Depends(get_single_ventilation),
):
    if 0 <= level <= 25:
        ventilation.setPermanentLevel("levelOne")
    elif 25 < level <= 50:
        ventilation.setPermanentLevel("levelTwo")
    elif 50 < level <= 75:
        ventilation.setPermanentLevel("levelThree")
    elif 75 < level <= 100:
        ventilation.setPermanentLevel("levelFour")
    else:
        raise HTTPException(status_code=404, detail="Unknown level")


@router.get("/program")
def get_program(ventilation: PyViCareVentilationDevice = Depends(get_single_ventilation)) -> str:
    return ventilation.getActiveProgram()
