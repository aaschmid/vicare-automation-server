from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from pyatv import Protocol
from pyatv.conf import ManualService

import app.dependencies as deps
from app.main import app


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
@patch("app.dependencies.scan", new_callable=AsyncMock)
async def test_appletv_scan_finds_no_device(mock_scan, dependency_mocker):
    deps._cached_appletv = None
    mock_scan.return_value = []

    result = await deps.get_appletv(dependency_mocker.settings)

    assert result is None
    assert deps._cached_appletv is None


@pytest.mark.parametrize("dependency_mocker", [[app, {"appletv_companion_credentials": "my_secret"}]], indirect=True)
@patch("app.dependencies.scan", new_callable=AsyncMock)
@patch("app.dependencies.connect", new_callable=AsyncMock)
async def test_appletv_connection_fails_after_scan(mock_connect, mock_scan, dependency_mocker):
    deps._cached_appletv = None

    mock_config = MagicMock()
    mock_config.services = [ManualService(None, Protocol.Companion, 42, None)]

    mock_connect.side_effect = Exception("connection failed")

    scanned_dev = MagicMock()
    svc = MagicMock()
    svc.protocol = deps.Protocol.Companion
    scanned_dev.services = [svc]
    mock_scan.return_value = [mock_config]

    result = await deps.get_appletv(dependency_mocker.settings)

    assert result is None
    assert deps._cached_appletv is None
    assert mock_config.services[0].credentials == "my_secret"


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
@patch("app.dependencies.scan", new_callable=AsyncMock)
@patch("app.dependencies.connect", new_callable=AsyncMock)
async def test_appletv_connects_after_scan(mock_connect, _mock_scan, dependency_mocker):
    deps._cached_appletv = None

    alive_atv = MagicMock()
    mock_connect.return_value = alive_atv

    result = await deps.get_appletv(dependency_mocker.settings)

    assert result == alive_atv
    assert deps._cached_appletv == alive_atv


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
@patch("app.dependencies.scan", new_callable=AsyncMock)
@patch("app.dependencies.connect", new_callable=AsyncMock)
async def test_appletv_cached_connection_dead_reconnects(mock_connect, mock_scan, dependency_mocker):
    dead_atv = MagicMock()
    type(dead_atv).power = PropertyMock(side_effect=Exception("Dead"))
    deps._cached_appletv = dead_atv

    alive_atv = MagicMock()
    mock_connect.return_value = alive_atv

    result = await deps.get_appletv(dependency_mocker.settings)

    assert result == alive_atv
    assert deps._cached_appletv == alive_atv
    dead_atv.close.assert_called_once()


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
@patch("app.dependencies.scan", new_callable=AsyncMock)
async def test_appletv_reuse_cached_connection(mock_scan, dependency_mocker):
    alive_atv = MagicMock()
    deps._cached_appletv = alive_atv

    mock_scan.side_effect = Exception("connection failed")

    result = await deps.get_appletv(dependency_mocker.settings)

    assert result == alive_atv
    assert deps._cached_appletv == alive_atv
    alive_atv.close.assert_not_called()
