import asyncio
import logging
from dataclasses import dataclass
from functools import lru_cache
from ipaddress import IPv4Address
from typing import Annotated

from fastapi import Depends
from pyatv import conf, connect
from pyatv.const import Protocol
from pyatv.interface import AppleTV
from PyViCare.PyViCare import PyViCare

from app.request_tracking import RequestTracker
from app.settings import Settings

logger = logging.getLogger(__name__)

_cached_appletv_connection: "AppleTvConnection | None" = None
_connection_lock = asyncio.Lock()


@lru_cache
def get_request_tracker() -> RequestTracker:
    """FastAPI dependency to get the request tracker singleton.

    Usage in route handlers:
        request_tracker: Annotated[RequestTracker, Depends(get_request_tracker)]
    """
    return RequestTracker()


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_vicare(settings: Annotated[Settings, Depends(get_settings)]) -> PyViCare:
    vicare = PyViCare()
    vicare.setCacheDuration(120)
    vicare.initWithCredentials(settings.email, settings.password, settings.client_id, "vicare.token")
    return vicare


@dataclass
class AppleTvConnection:
    atv: AppleTV
    host: IPv4Address
    port: int


CONNECTION_TRYING_TIMEOUT = 2.0
PORT_START = 49152
PORT_END = PORT_START + 49


async def get_appletv_connection(settings: Annotated[Settings, Depends(get_settings)]) -> AppleTvConnection | None:
    global _cached_appletv_connection

    async with _connection_lock:
        last_port = None
        if _cached_appletv_connection is not None:
            try:
                _ = _cached_appletv_connection.atv.power.power_state
                logger.debug("Using cached connection")
                return _cached_appletv_connection
            except Exception:
                logger.info("Cached connection dead, will reconnect")
                last_port = _cached_appletv_connection.port
                await teardown_cached_appletv_connection()

        if last_port is not None:
            logger.debug(f"Trying cached port {last_port}")
            atv = await _try_to_connect_to_appletv_on_port(last_port, settings)
            if atv:
                logger.info(f"Reconnected using cached port {last_port}")
                _cached_appletv_connection = AppleTvConnection(atv, settings.appletv_host, last_port)
                return _cached_appletv_connection
            logger.info(f"Last port {last_port} no longer works")

        logger.info(
            f"Scanning for Apple TV port (range {PORT_START}-{PORT_END}" + f" without cached port {last_port})"
            if last_port
            else ")"
        )
        for port in range(PORT_START, PORT_END + 1):
            if last_port and port == last_port:
                logger.debug(f"Skipping port {port} as already tried above because cached")
                continue

            logger.debug(f"Trying port {port}")
            atv = await _try_to_connect_to_appletv_on_port(port, settings)
            if atv:
                logger.info(f"Found AppleTV service on port {port} and connected to it")
                _cached_appletv_connection = AppleTvConnection(atv, settings.appletv_host, port)
                return _cached_appletv_connection

        logger.warning(f"No working connection to AppleTV found on {settings.appletv_host}")
        return None


async def teardown_cached_appletv_connection() -> None:
    global _cached_appletv_connection

    if _cached_appletv_connection is not None:
        try:
            await asyncio.gather(*_cached_appletv_connection.atv.close())
            logger.info("Apple TV connection closed")
        except Exception:
            logger.info("Apple TV connection closing failed", exc_info=True)
    _cached_appletv_connection = None


async def _try_to_connect_to_appletv_on_port(port: int, settings: Settings) -> AppleTV | None:
    logger.debug(f"Attempting connection to {settings.appletv_host}:{port}")

    config = conf.AppleTV(settings.appletv_host, "Auto")
    config.add_service(
        conf.ManualService(
            settings.appletv_companion_identifier,
            Protocol.Companion,
            port,
            {},
            credentials=settings.appletv_companion_credentials,
        )
    )

    try:
        return await asyncio.wait_for(connect(config, asyncio.get_running_loop()), timeout=CONNECTION_TRYING_TIMEOUT)
    except TimeoutError:
        logger.debug(f"Connection to port {port} timed out after {CONNECTION_TRYING_TIMEOUT}s.")
        return None
    except Exception as e:
        logger.debug(f"Connection to port {port} failed: {type(e).__name__}: {e}")
        return None
