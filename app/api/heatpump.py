from fastapi import APIRouter, Depends, HTTPException
from PyViCare import PyViCareDeviceConfig, PyViCareHeatPump
from PyViCare.PyViCareHeatPump import Compressor

from app.api.heating import ROUTE_PREFIX_HEATING, get_single_heating_device

ROUTE_PREFIX_HEATING_HEATPUMP = f"{ROUTE_PREFIX_HEATING}/heatpump"
router = APIRouter(prefix=ROUTE_PREFIX_HEATING_HEATPUMP)


def get_single_heatpump(device: PyViCareDeviceConfig = Depends(get_single_heating_device)) -> PyViCareHeatPump:
    return device.asHeatPump()


def get_single_compressor(heatpump: PyViCareHeatPump = Depends(get_single_heatpump)) -> Compressor:
    if len(heatpump.compressors) <= 0:
        raise HTTPException(422, "No compressor found for heatpump.")
    if len(heatpump.compressors) > 1:
        raise HTTPException(422, "Multiple compressors found, currently unsupported.")
    return heatpump.compressors[0]


@router.get("/")
def get_heatpump(
    device: PyViCareDeviceConfig = Depends(get_single_heating_device),
    heatpump: PyViCareHeatPump = Depends(get_single_heatpump),
    compressor: Compressor = Depends(get_single_compressor),
) -> dict:
    return {
        "device": {
            "boilerSerial": heatpump.getBoilerSerial(),
            "controllerSerial": heatpump.getControllerSerial(),
            "deviceId": device.device_id,
            "model": device.device_model,
            "serial": device.service.accessor.serial,
        },
        "compressor": {
            "active": compressor.getActive(),
            "hours": compressor.getHours(),
            "phase": compressor.getPhase(),
            "starts": compressor.getStarts(),
        },
        "errors": device.service.getProperty("device.messages.errors.raw")["properties"]["entries"]["value"],
        "temperature": {
            "buffer": heatpump.getBufferMainTemperature(),
            "outside": heatpump.getOutsideTemperature(),
            "primaryCircuitSupply": heatpump.getSupplyTemperaturePrimaryCircuit(),
            "return": heatpump.getReturnTemperature(),
            "secondaryCircuitSupply": heatpump.getSupplyTemperatureSecondaryCircuit(),
        },
        "status": device.status,
    }
