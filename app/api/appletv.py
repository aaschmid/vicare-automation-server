import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.appletv import AppleTvClient, SystemStatus
from app.dependencies import get_appletv

logger = logging.getLogger(__name__)

ROUTE_PREFIX_APPLETV = "/appletv"

router = APIRouter(prefix=ROUTE_PREFIX_APPLETV)


@router.get("")
async def get_state(appletv: Annotated[AppleTvClient, Depends(get_appletv)]) -> dict:
    system_status = await appletv.system_status()
    if system_status is None:
        logger.warning("Apple TV connection not available")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AppleTV connection not available")

    return {
        "active": 1 if system_status not in {SystemStatus.Asleep, SystemStatus.Unknown} else 0,
        "atv": appletv.connection_info(),
        "idle": 1 if system_status == SystemStatus.Idle else 0,
        "state": system_status.name.lower(),
        "screensaver": 1 if system_status == SystemStatus.Screensaver else 0,
    }
