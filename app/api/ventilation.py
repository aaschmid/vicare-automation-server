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
def get_ventilation(device: PyViCareDeviceConfig = Depends(get_single_ventilation_device)) -> dict:
    # TODO: create methods in PyViCare to access properties easier
    level_strings = ["one", "two", "three", "four"]
    levels = {
        level: device.service.getProperty(f"ventilation.operating.programs.level{level.capitalize()}")["properties"]
        for level in level_strings
    }
    active_levels = [level for level, v in levels.items() if v["active"]["value"]]
    if len(active_levels) != 1:
        raise HTTPException(status_code=422, detail=f"Couldn't find active level, was {active_levels}.")
    active_level = active_levels[0]

    errors = device.service.getProperty("device.messages.errors.raw")["properties"]["entries"]["value"]
    filter_change = device.service.getProperty("ventilation.operating.modes.filterChange")["properties"]["active"][
        "value"
    ]
    return {
        "active": 1 if device.status.lower() == "online" else 0,
        "device": {
            "deviceId": device.device_id,
            "model": device.device_model,
            "productIdentification": device.service.getProperty("device.productIdentification")["properties"][
                "product"
            ]["value"],
            "serial": device.service.accessor.serial,
        },
        "errors": errors,
        "errorCount": len(errors),
        "filterChange": 1 if filter_change else 0,
        "levels": {"active": active_level, "activeNo": level_strings.index(active_level) + 1}
        | {
            level: {
                "active": 1 if v["active"]["value"] else 0,
                "volumeFlow": f"{v['volumeFlow']['value']} {v['volumeFlow']['unit']}",
            }
            for level, v in levels.items()
        },
        "status": device.status,
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
