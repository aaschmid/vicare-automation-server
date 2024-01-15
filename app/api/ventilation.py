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
    levels = {
        level: device.service.getProperty(f"ventilation.operating.programs.level{level.capitalize()}")["properties"]
        for level in ["one", "two", "three", "four"]
    }
    return {
        "device": {
            "deviceId": device.device_id,
            "model": device.device_model,
            "productIdentification": device.service.getProperty("device.productIdentification")["properties"][
                "product"
            ]["value"],
            "serial": device.service.accessor.serial,
        },
        "errors": device.service.getProperty("device.messages.errors.raw")["properties"]["entries"]["value"],
        "filterChange": device.service.getProperty("ventilation.operating.modes.filterChange")["properties"]["active"][
            "value"
        ],
        "levels": {
            level: {
                "active": v["active"]["value"],
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
