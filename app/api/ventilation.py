from fastapi import APIRouter, Depends, HTTPException
from PyViCare import PyViCareDeviceConfig, PyViCareVentilationDevice
from PyViCare.PyViCare import PyViCare

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


@router.get("/")
def get_ventilation(device: PyViCareDeviceConfig = Depends(get_single_ventilation_device)) -> dict:
    return {
        "deviceId": device.device_id,
        "model": device.device_model,
        "serial": device.service.accessor.serial,
        "status": device.status,
    }


@router.get("/mode")
def get_mode(ventilation: PyViCareVentilationDevice = Depends(get_single_ventilation)) -> str:
    return ventilation.getActiveMode()


@router.get("/program")
def get_program(ventilation: PyViCareVentilationDevice = Depends(get_single_ventilation)) -> str:
    return ventilation.getActiveProgram()
