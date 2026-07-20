import asyncio
import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pyatv import connect, scan
from pyatv.const import Protocol
from pyatv.interface import AppleTV
from PyViCare.PyViCare import PyViCare

from app.request_tracking import RequestTracker
from app.settings import Settings

logger = logging.getLogger(__name__)

_cached_appletv: AppleTV | None = None


@lru_cache()
def get_request_tracker() -> RequestTracker:
    """FastAPI dependency to get the request tracker singleton.

    Usage in route handlers:
        request_tracker: Annotated[RequestTracker, Depends(get_request_tracker)]
    """
    return RequestTracker()


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_vicare(settings: Annotated[Settings, Depends(get_settings)]) -> PyViCare:
    vicare = PyViCare()
    vicare.setCacheDuration(120)
    vicare.initWithCredentials(settings.email, settings.password, settings.client_id, "vicare.token")
    return vicare


async def get_appletv(settings: Annotated[Settings, Depends(get_settings)]) -> AppleTV | None:
    global _cached_appletv

    if _cached_appletv is not None:
        try:
            _ = _cached_appletv.power.power_state
            return _cached_appletv
        except Exception:
            logger.info("Cached AppleTV connection dead, reconnecting", exc_info=True)
            await teardown_appletv()

    loop = asyncio.get_running_loop()
    devices = await scan(loop, hosts=[str(settings.appletv_host)], protocol=Protocol.Companion)
    if not devices:
        logger.warning("AppleTV not found during scan")
        return None

    dev = devices[0]
    for svc in dev.services:
        if svc.protocol == Protocol.Companion:
            svc.credentials = settings.appletv_companion_credentials

    try:
        atv = await connect(dev, loop)
    except Exception:
        logger.warning("AppleTV connection failed", exc_info=True)
        return None

    _cached_appletv = atv
    return atv


async def teardown_appletv() -> None:
    global _cached_appletv
    if _cached_appletv is not None:
        try:
            await asyncio.gather(*_cached_appletv.close())
        except Exception:
            logger.info("AppleTV connection closing failed", exc_info=True)
    _cached_appletv = None
