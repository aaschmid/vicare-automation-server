"""AppleTV connection abstraction.

Owns a single companion-link connection to an AppleTV, keeps its system status fresh by
re-querying the device on each call (pyatv's cached ``power_state`` only updates via push
events and goes stale when those stop arriving), and reconnects transparently when the
connection dies or the companion port drifts. Callers see ``system_status()`` and the
connection metadata, never the plumbing.
"""

import asyncio
import logging
import time

from pyatv import conf, connect
from pyatv.const import Protocol
from pyatv.interface import AppleTV
from pyatv.protocols.companion.api import SystemStatus

from app.settings import Settings

logger = logging.getLogger(__name__)

__all__ = ["AppleTvClient", "SystemStatus"]


CONNECT_TIMEOUT = 2.0
FETCH_TIMEOUT = 3.0
PORT_START = 49152
PORT_END = PORT_START + 49
SCAN_COOLDOWN = 60.0


class AppleTvClient:
    """Manages a companion-link connection to an AppleTV and reports its system status."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._atv: AppleTV | None = None
        self._port: int | None = None
        self._last_scan_failed_at: float | None = None
        self._lock = asyncio.Lock()

    def connection_info(self) -> dict:
        """Connection metadata for API responses (host/port/status)."""
        return {
            "host": str(self._settings.appletv_host),
            "port": self._port,
            "status": "connected" if self._atv is not None else "disconnected",
        }

    async def system_status(self) -> SystemStatus | None:
        """Current device system status, reconnecting transparently on failure.

        Returns ``None`` when the device is unreachable, so callers can map that to e.g. 503
        without seeing the reconnect/port-scan plumbing.
        """
        async with self._lock:
            if self._atv is not None:
                try:
                    return await self._fetch_system_status()
                except Exception:
                    logger.info("AppleTV fetch failed, reconnecting", exc_info=True)

            if await self._reconnect():
                return await self._fetch_system_status()
            return None

    async def close(self) -> None:
        async with self._lock:
            await self._close()

    async def _close(self) -> None:
        if self._atv is not None:
            try:
                await asyncio.gather(*self._atv.close())
                logger.info("AppleTV connection closed")
            except Exception:
                logger.info("AppleTV connection closing failed", exc_info=True)
        self._atv = None
        self._port = None

    async def _reconnect(self) -> bool:
        # Owns the whole connect process: tear down any former connection, try its cached port,
        # then fall back to a full port scan. Handles both initial connect and reconnect.
        last_port = self._port
        await self._close()

        if last_port is not None:
            logger.debug(f"Trying cached port {last_port}")
            atv = await self._try_connect(last_port)
            if atv is not None:
                logger.info(f"Reconnected using cached port {last_port}")
                self._last_scan_failed_at = None
                self._atv = atv
                self._port = last_port
                return True
            logger.info(f"Cached port {last_port} no longer works")

        if self._last_scan_failed_at is not None and (time.monotonic() - self._last_scan_failed_at) < SCAN_COOLDOWN:
            logger.info(
                f"Skipping scan, last full scan failed {time.monotonic() - self._last_scan_failed_at:.1f}s ago "
                f"(cooldown {SCAN_COOLDOWN}s)"
            )
            return False

        logger.info(
            f"Scanning for Apple TV port (range {PORT_START}-{PORT_END}"
            + (f" without cached port {last_port})" if last_port else ")")
        )
        for port in range(PORT_START, PORT_END + 1):
            if port == last_port:
                logger.debug(f"Skipping port {port} as already tried above because cached")
                continue
            logger.debug(f"Trying port {port}")
            atv = await self._try_connect(port)
            if atv is not None:
                logger.info(f"Found AppleTV service on port {port} and connected to it")
                self._last_scan_failed_at = None
                self._atv = atv
                self._port = port
                return True

        logger.warning(f"No working connection to AppleTV found on {self._settings.appletv_host}")
        self._last_scan_failed_at = time.monotonic()
        return False

    async def _try_connect(self, port: int) -> AppleTV | None:
        logger.debug(f"Attempting connection to {self._settings.appletv_host}:{port}")
        config = conf.AppleTV(self._settings.appletv_host, "Auto")
        config.add_service(
            conf.ManualService(
                self._settings.appletv_companion_identifier,
                Protocol.Companion,
                port,
                {},
                credentials=self._settings.appletv_companion_credentials,
            )
        )
        try:
            return await asyncio.wait_for(connect(config, asyncio.get_running_loop()), timeout=CONNECT_TIMEOUT)
        except TimeoutError:
            logger.debug(f"Connection to port {port} timed out after {CONNECT_TIMEOUT}s.")
            return None
        except Exception as e:
            logger.debug(f"Connection to port {port} failed: {type(e).__name__}: {e}")
            return None

    async def _fetch_system_status(self) -> SystemStatus:
        # pyatv's CompanionPower.power_state is cached at connect time and only refreshed via push
        # events over the companion socket; re-run the one-shot fetch it uses at connect time.
        companion_power = self._atv.power.main_instance  # type: ignore[union-attr, attr-defined]
        return await asyncio.wait_for(companion_power.api.fetch_attention_state(), timeout=FETCH_TIMEOUT)
