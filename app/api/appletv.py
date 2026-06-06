from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pyatv.const import PowerState
from pyatv.interface import AppleTV
from starlette import status

from app import dependencies

ROUTE_PREFIX_APPLETV = "/appletv"

router = APIRouter(prefix=ROUTE_PREFIX_APPLETV)


@router.get("")
def get_state(atv: Annotated[AppleTV | None, Depends(dependencies.get_appletv)]) -> dict:
    if atv is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AppleTV connection not available")

    return {
        "active": 1 if atv.power.power_state == PowerState.On else 0,
    }
