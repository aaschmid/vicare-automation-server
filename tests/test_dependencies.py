from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pyatv.const import Protocol

import app.appletv as appletv_mod
from app.appletv import AppleTvClient, SystemStatus
from app.main import app

PORT = appletv_mod.PORT_START  # 49152
TARGET_PORT = PORT + 1  # 49153


def _settings() -> MagicMock:
    s = MagicMock()
    s.appletv_host = "192.168.1.100"
    s.appletv_companion_identifier = "id42"
    s.appletv_companion_credentials = "test-credentials"
    return s


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_reuses_live_connection_and_refreshes_status(dependency_mocker):
    settings = _settings()
    client = AppleTvClient(settings)
    alive_atv = MagicMock()
    client._atv = alive_atv
    client._port = TARGET_PORT

    fetch = AsyncMock(return_value=SystemStatus.Awake)
    client._fetch_system_status = fetch  # type: ignore[method-assign]

    with patch("app.appletv.connect", new_callable=AsyncMock) as patched:
        status = await client.system_status()

    assert status == SystemStatus.Awake
    assert client._atv is alive_atv
    assert client._port == TARGET_PORT
    fetch.assert_awaited_once_with()
    patched.assert_not_called()  # no reconnect when the live fetch succeeds


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_reconnects_using_cached_port_after_dead_connection(dependency_mocker):
    settings = _settings()
    client = AppleTvClient(settings)
    dead_atv = MagicMock()
    client._atv = dead_atv
    client._port = TARGET_PORT

    alive_atv = MagicMock()

    # cached fetch fails -> reconnect tries only cached port -> succeeds -> fetch succeeds
    fetch_calls = []

    def _fetch_side_effect():
        fetch_calls.append(None)
        if len(fetch_calls) == 1:
            raise Exception("Dead")  # first call on the dead cached connection
        return SystemStatus.Awake  # second call on the reconnected connection

    client._fetch_system_status = AsyncMock(side_effect=_fetch_side_effect)  # type: ignore[method-assign]

    with patch("app.appletv.connect", new_callable=AsyncMock, return_value=alive_atv) as patched:
        status = await client.system_status()

    assert status == SystemStatus.Awake
    assert client._atv is alive_atv
    assert client._port == TARGET_PORT
    # reconnect only tries the cached port, not the whole range
    assert patched.call_count == 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_full_scan_finds_no_device(dependency_mocker):
    settings = _settings()
    client = AppleTvClient(settings)

    with patch(
        "app.appletv.connect",
        new_callable=AsyncMock,
        side_effect=ConnectionError("connection refused"),
    ) as patched:
        status = await client.system_status()

    assert status is None
    assert client._atv is None
    assert client._port is None
    assert patched.call_count == appletv_mod.PORT_END - appletv_mod.PORT_START + 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_full_scan_connects_after_trying_ports(dependency_mocker):
    settings = _settings()
    client = AppleTvClient(settings)
    client._fetch_system_status = AsyncMock(return_value=SystemStatus.Awake)  # type: ignore[method-assign]

    alive_atv = MagicMock()

    def _connect_side_effect(config, _loop):
        service = next(s for s in config.services if s.protocol == Protocol.Companion)
        return alive_atv if service.port == TARGET_PORT else None

    with patch("app.appletv.connect", new_callable=AsyncMock, side_effect=_connect_side_effect) as patched:
        status = await client.system_status()

    assert status == SystemStatus.Awake
    assert client._atv is alive_atv
    assert client._port == TARGET_PORT
    # scan starts at PORT_START; target is PORT+1, so 2 attempts
    assert patched.call_count == TARGET_PORT - appletv_mod.PORT_START + 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_dead_cached_port_falls_back_to_full_scan(dependency_mocker):
    settings = _settings()
    client = AppleTvClient(settings)
    dead_atv = MagicMock()
    client._atv = dead_atv
    client._port = PORT  # cached port that will fail to reconnect

    alive_atv = MagicMock()

    fetch_calls = []

    def _fetch_side_effect():
        fetch_calls.append(None)
        if len(fetch_calls) == 1:
            raise Exception("Dead")  # first call on the dead cached connection
        return SystemStatus.Awake  # second call on the reconnected connection

    client._fetch_system_status = AsyncMock(side_effect=_fetch_side_effect)  # type: ignore[method-assign]

    target_port = PORT + 1  # cached port fails, next port in the range succeeds

    def _connect_side_effect(config, _loop):
        service = next(s for s in config.services if s.protocol == Protocol.Companion)
        return alive_atv if service.port == target_port else None

    with patch("app.appletv.connect", new_callable=AsyncMock, side_effect=_connect_side_effect) as patched:
        status = await client.system_status()

    assert status == SystemStatus.Awake
    assert client._atv is alive_atv
    assert client._port == target_port
    # cached port tried once (fails), then scan PORT_START..target_port excluding cached port
    # target_port == PORT_START+1: scan tries PORT_START (fail) then target_port (success) = 2 + 1 = 3
    assert patched.call_count == 1 + (target_port - appletv_mod.PORT_START + 1) - 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_connection_timeout_returns_none(dependency_mocker):
    settings = _settings()
    client = AppleTvClient(settings)

    with patch("app.appletv.connect", new_callable=AsyncMock, side_effect=TimeoutError()):
        status = await client.system_status()

    assert status is None
    assert client._atv is None
    assert client._port is None


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_failed_scan_is_cooldown_cached(dependency_mocker):
    settings = _settings()
    client = AppleTvClient(settings)

    with patch(
        "app.appletv.connect",
        new_callable=AsyncMock,
        side_effect=ConnectionError("connection refused"),
    ) as patched:
        first = await client.system_status()
        second = await client.system_status()

    assert first is None
    assert second is None
    # first call scans the whole range; second is within cooldown and must not scan
    assert patched.call_count == appletv_mod.PORT_END - appletv_mod.PORT_START + 1
    assert client._last_scan_failed_at is not None


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_connect_passes_credentials_from_settings(dependency_mocker):
    settings = _settings()
    settings.appletv_companion_credentials = "my_secret"
    client = AppleTvClient(settings)

    with patch("app.appletv.connect", new_callable=AsyncMock, return_value=None) as patched:
        await client.system_status()

    for call in patched.call_args_list:
        config = call.args[0]
        service = next(s for s in config.services if s.protocol == Protocol.Companion)
        assert service.credentials == "my_secret"
