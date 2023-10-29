from fastapi import APIRouter, Depends, HTTPException
from PyViCare import PyViCareDeviceConfig, PyViCareHeatPump
from PyViCare.PyViCare import PyViCare

from app import dependencies

ROUTE_PREFIX_HEATPUMP = "/heatpump"
router = APIRouter(prefix=ROUTE_PREFIX_HEATPUMP)


def get_single_heatpump_device(vicare: PyViCare = Depends(dependencies.get_vicare)) -> PyViCareDeviceConfig:
    result = [d for d in vicare.devices if "type:heatpump" in d.service.roles]
    if len(result) <= 0:
        raise HTTPException(422, "No heatpump device found.")
    if len(result) > 1:
        raise HTTPException(422, "Multiple heatpump devices found, currently unsupported.")
    return result[0]


def get_single_heatpump(vicare: PyViCare = Depends(dependencies.get_vicare)) -> PyViCareHeatPump:
    return get_single_heatpump_device(vicare).asHeatPump()


@router.get("/")
def get_heatpump(device: PyViCareDeviceConfig = Depends(get_single_heatpump_device)) -> dict:
    return {
        "deviceId": device.device_id,
        "model": device.device_model,
        "serial": device.service.accessor.serial,
        "status": device.status,
    }


@router.get("/temperature")
def get_temperature(heatpump: PyViCareHeatPump = Depends(get_single_heatpump)) -> dict:
    return {
        "outside": heatpump.getOutsideTemperature(),
        "return": heatpump.getReturnTemperature(),
    }


@router.get("/temperature/outside")
def get_temperature_outside(heatpump: PyViCareHeatPump = Depends(get_single_heatpump)) -> float:
    return heatpump.getOutsideTemperature()


@router.get("/temperature/return")
def get_temperature_return(heatpump: PyViCareHeatPump = Depends(get_single_heatpump)) -> float:
    return heatpump.getReturnTemperature()
