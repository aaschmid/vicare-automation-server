import enum
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from PyViCare import PyViCare
from PyViCare.PyViCareHeatingDevice import HeatingDevice
from starlette import status

from app import dependencies
from app.api.heating import ROUTE_PREFIX_HEATING, get_single_heating_device
from app.api.types import HeatingCommand

ROUTE_PREFIX_HEATING_DHW = f"{ROUTE_PREFIX_HEATING}/dhw"
router = APIRouter(prefix=ROUTE_PREFIX_HEATING_DHW)


class HeatingDomesticHotWaterLevel(enum.Enum):
    Main = "main"
    Temp2 = "temp2"


def get_single_heating(vicare: PyViCare = Depends(dependencies.get_vicare)) -> HeatingDevice:
    return get_single_heating_device(vicare).asGeneric()


@router.get("")
def get_dhw(heating: HeatingDevice = Depends(get_single_heating)) -> dict:
    return {
        "active": 1 if heating.getDomesticHotWaterActive() else 0,
        "chargingActive": 1 if heating.getDomesticHotWaterChargingActive() else 0,
        "levels": {
            "main": heating.getDomesticHotWaterConfiguredTemperature(),
            "max": heating.getDomesticHotWaterMaxTemperature(),
            "min": heating.getDomesticHotWaterMinTemperature(),
            "temp2": heating.getDomesticHotWaterConfiguredTemperature2(),
        },
        "oneTimeCharge": 1 if heating.getOneTimeCharge() else 0,
        "pumps": {
            "circulationActive": 1 if heating.getDomesticHotWaterCirculationPumpActive() else 0,
            "mode": heating.getDomesticHotWaterCirculationMode(),
        },
        "storageTemperature": heating.getDomesticHotWaterStorageTemperature(),
    }


@router.put("/onetimecharge", status_code=status.HTTP_204_NO_CONTENT)
def set_one_time_charge(
    command: Annotated[HeatingCommand, Body()],
    heating: HeatingDevice = Depends(get_single_heating),
):
    if command == HeatingCommand.Activate:
        heating.activateOneTimeCharge()
    elif command == HeatingCommand.Deactivate:
        heating.deactivateOneTimeCharge()


@router.put("/level/{level}/{temperature}", status_code=status.HTTP_204_NO_CONTENT)
def set_level_temperature(
    level: Annotated[HeatingDomesticHotWaterLevel, Path(title="The heating circuit program")],
    temperature: Annotated[int, Path(title="The temperature of the provided heating circuit program", ge=10, le=60)],
    heating: HeatingDevice = Depends(get_single_heating),
):
    if level == HeatingDomesticHotWaterLevel.Main:
        heating.setDomesticHotWaterTemperature(temperature)
    elif level == HeatingDomesticHotWaterLevel.Temp2:
        heating.setDomesticHotWaterTemperature2(temperature)
