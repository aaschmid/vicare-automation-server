from typing import Annotated

from fastapi import APIRouter, Depends
from pyatv.const import PowerState
from pyatv.interface import AppleTV

from app import dependencies

ROUTE_PREFIX_APPLETV = "/appletv"

router = APIRouter(prefix=ROUTE_PREFIX_APPLETV)


@router.get("")
def get_state(atv: Annotated[AppleTV | None, Depends(dependencies.get_appletv)]) -> dict:
    if not atv:
        return {"active": -1}

    return {
        "active": 1 if atv.power.power_state == PowerState.On else 0,
    }
