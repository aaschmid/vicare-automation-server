from fastapi.testclient import TestClient

from app.api.appletv import ROUTE_PREFIX_APPLETV
from app.api.circuit import ROUTE_PREFIX_HEATING_CIRCUIT
from app.api.dhw import ROUTE_PREFIX_HEATING_DHW
from app.api.health import ROUTE_PREFIX_HEALTH
from app.api.heatpump import ROUTE_PREFIX_HEATING_HEATPUMP
from app.api.ventilation import ROUTE_PREFIX_VENTILATION
from app.main import app

client = TestClient(app)


def test_app_should_have_circuit_route():
    routes = [r for r in app.openapi()["paths"] if r.startswith(ROUTE_PREFIX_HEATING_CIRCUIT)]
    assert len(routes) > 0


def test_app_should_have_dhw_route():
    routes = [r for r in app.openapi()["paths"] if r.startswith(ROUTE_PREFIX_HEATING_DHW)]
    assert len(routes) > 0


def test_app_should_have_health_route():
    routes = [r for r in app.openapi()["paths"] if r.startswith(ROUTE_PREFIX_HEALTH)]
    assert len(routes) > 0


def test_app_should_have_heatpump_route():
    routes = [r for r in app.openapi()["paths"] if r.startswith(ROUTE_PREFIX_HEATING_HEATPUMP)]
    assert len(routes) > 0


def test_app_should_have_ventilation_route():
    routes = [r for r in app.openapi()["paths"] if r.startswith(ROUTE_PREFIX_VENTILATION)]
    assert len(routes) > 0


def test_app_should_have_appletv_route():
    routes = [r for r in app.openapi()["paths"] if r.startswith(ROUTE_PREFIX_APPLETV)]
    assert len(routes) > 0
