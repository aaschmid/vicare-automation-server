from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from pyatv.const import Protocol

import app.dependencies as deps
from app.main import app

PORT = 49153


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_reuse_cached_connection(dependency_mocker):
    alive_atv = MagicMock()
    alive_connection = deps.AppleTvConnection(alive_atv, dependency_mocker.settings.appletv_host, PORT)
    deps._cached_appletv_connection = alive_connection

    with patch("app.dependencies.connect", new_callable=AsyncMock) as patched:
        result = await deps.get_appletv_connection(dependency_mocker.settings)

    assert result == alive_connection
    assert deps._cached_appletv_connection == alive_connection
    patched.assert_not_called()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_reconnects_using_cached_port_after_dead_connection(dependency_mocker):
    dead_atv = MagicMock()
    type(dead_atv).power = PropertyMock(side_effect=Exception("Dead"))
    deps._cached_appletv_connection = deps.AppleTvConnection(dead_atv, dependency_mocker.settings.appletv_host, PORT)

    alive_atv = MagicMock()

    with patch("app.dependencies.connect", new_callable=AsyncMock, return_value=alive_atv) as patched:
        result = await deps.get_appletv_connection(dependency_mocker.settings)

    assert result is not None
    assert result.atv == alive_atv
    assert result.port == PORT
    assert deps._cached_appletv_connection is result
    # Reconnect should only try the cached port, not scan the whole range
    assert patched.call_count == 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_full_scan_finds_no_device(dependency_mocker):
    deps._cached_appletv_connection = None

    with patch(
        "app.dependencies.connect", new_callable=AsyncMock, side_effect=ConnectionError("connection refused")
    ) as patched:
        result = await deps.get_appletv_connection(dependency_mocker.settings)

    assert result is None
    assert deps._cached_appletv_connection is None
    assert patched.call_count == deps.PORT_END - deps.PORT_START + 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_full_scan_connects_after_trying_ports(dependency_mocker):
    deps._cached_appletv_connection = None

    alive_atv = MagicMock()
    target_port = PORT  # succeeds on the second port tried in the range (PORT_START, then PORT)

    def _connect_side_effect(config, _loop):
        # Succeed only on the target port, fail (return None) for all others
        service = next(s for s in config.services if s.protocol == Protocol.Companion)
        return alive_atv if service.port == target_port else None

    with patch("app.dependencies.connect", new_callable=AsyncMock, side_effect=_connect_side_effect) as patched:
        result = await deps.get_appletv_connection(dependency_mocker.settings)

    assert result is not None
    assert result.atv == alive_atv
    assert result.port == target_port
    assert deps._cached_appletv_connection is result
    # Scan starts at PORT_START; target is PORT, so PORT - PORT_START + 1 attempts
    assert patched.call_count == target_port - deps.PORT_START + 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_dead_cached_port_falls_back_to_full_scan(dependency_mocker):
    dead_atv = MagicMock()
    type(dead_atv).power = PropertyMock(side_effect=Exception("Dead"))
    deps._cached_appletv_connection = deps.AppleTvConnection(dead_atv, dependency_mocker.settings.appletv_host, PORT)

    alive_atv = MagicMock()
    target_port = PORT + 1  # cached port fails, next port in the range succeeds

    def _connect_side_effect(config, _loop):
        service = next(s for s in config.services if s.protocol == Protocol.Companion)
        return alive_atv if service.port == target_port else None

    with patch("app.dependencies.connect", new_callable=AsyncMock, side_effect=_connect_side_effect) as patched:
        result = await deps.get_appletv_connection(dependency_mocker.settings)

    assert result is not None
    assert result.atv == alive_atv
    assert result.port == target_port
    assert deps._cached_appletv_connection is result
    # Cached port tried once (fails, skipped during scan), then scan tries
    # PORT_START..target_port excluding the cached port. target_port == PORT_START+1,
    # so the scan tries PORT_START (fail) then target_port (success) = 2 calls + 1 = 3.
    assert patched.call_count == 1 + (target_port - deps.PORT_START + 1) - 1


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
async def test_connection_timeout_returns_none(dependency_mocker):
    deps._cached_appletv_connection = None

    with patch("app.dependencies.connect", new_callable=AsyncMock, side_effect=TimeoutError()):
        result = await deps.get_appletv_connection(dependency_mocker.settings)

    assert result is None
    assert deps._cached_appletv_connection is None


@pytest.mark.parametrize("dependency_mocker", [[app, {"appletv_companion_credentials": "my_secret"}]], indirect=True)
async def test_connect_passes_credentials_from_settings(dependency_mocker):
    deps._cached_appletv_connection = None

    with patch("app.dependencies.connect", new_callable=AsyncMock, return_value=None) as patched:
        await deps.get_appletv_connection(dependency_mocker.settings)

    for call in patched.call_args_list:
        config = call.args[0]
        service = next(s for s in config.services if s.protocol == Protocol.Companion)
        assert service.credentials == "my_secret"
