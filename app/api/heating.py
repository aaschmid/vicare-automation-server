from fastapi import Depends, HTTPException
from PyViCare import PyViCareDeviceConfig
from PyViCare.PyViCare import PyViCare

from app import dependencies

ROUTE_PREFIX_HEATING = "/heating"


def get_single_heating_device(vicare: PyViCare = Depends(dependencies.get_vicare)) -> PyViCareDeviceConfig:
    result = [d for d in vicare.devices if "type:heatpump" in d.service.roles]
    if len(result) <= 0:
        raise HTTPException(422, "No heating device found.")
    if len(result) > 1:
        raise HTTPException(422, "Multiple heating devices found, currently unsupported.")
    return result[0]
