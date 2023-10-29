from fastapi.testclient import TestClient

from app.api.health import ROUTE_PREFIX_HEALTH
from app.api.heatpump import ROUTE_PREFIX_HEATPUMP
from app.main import app

client = TestClient(app)


def test_app_should_have_health_route():
    routes = [r for r in app.routes if r.path.startswith(ROUTE_PREFIX_HEALTH)]
    assert len(routes) > 0


def test_app_should_have_heatpump_route():
    routes = [r for r in app.routes if r.path.startswith(ROUTE_PREFIX_HEATPUMP)]
    assert len(routes) > 0
