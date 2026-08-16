import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pyatv.const import PowerState
from starlette import status

from app.dependencies import (
    AppleTvConnection,
    get_appletv_connection,
)

logger = logging.getLogger(__name__)

ROUTE_PREFIX_APPLETV = "/appletv"

router = APIRouter(prefix=ROUTE_PREFIX_APPLETV)


@router.get("")
def get_state(atv_connection: Annotated[AppleTvConnection | None, Depends(get_appletv_connection)]) -> dict:
    if atv_connection is None:
        logger.warning("Apple TV connection not available")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AppleTV connection not available")

    return {
        "atv": {
            "host": str(atv_connection.host),
            "port": atv_connection.port,
            "status": "connected",
        },
        "active": 1 if atv_connection.atv.power.power_state == PowerState.On else 0,
    }
