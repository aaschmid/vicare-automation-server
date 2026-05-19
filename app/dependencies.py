import asyncio
from functools import lru_cache
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from pyatv import Protocol, conf, connect
from pyatv.interface import AppleTV
from PyViCare.PyViCare import PyViCare

from app.request_tracking import RequestTracker
from app.settings import Settings


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


@lru_cache()
def get_appletv_config(settings: Annotated[Settings, Depends(get_settings)]) -> conf.AppleTV:
    config = conf.AppleTV(settings.appletv_host, "Unknown")
    config.add_service(
        conf.ManualService(
            settings.appletv_companion_identifier,
            Protocol.Companion,
            settings.appletv_companion_port,
            {},
            credentials=settings.appletv_companion_credentials,
        )
    )
    return config


async def get_appletv(config: Annotated[conf.AppleTV, Depends(get_appletv_config)]) -> AsyncGenerator[AppleTV | None]:
    loop = asyncio.get_running_loop()

    atv = await connect(config, loop)
    yield atv
    atv.close()
