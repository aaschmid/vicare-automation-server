import time
import typing as t
from datetime import timedelta

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from PyViCare.PyViCare import PyViCare

from app import dependencies

# TODO maybe use basic auth? configured?
start_time = time.time()

ROUTE_PREFIX_HEALTH = "/health"

router = APIRouter(prefix=ROUTE_PREFIX_HEALTH)


# TODO: letzter erfolgreichen Request auch integrieren?


class ViessmannApiModel(BaseModel):
    online: bool
    response_time_in_s: str
    installations_found: bool


class ChecksModel(BaseModel):
    auth_token: t.Literal["invalid"] | t.Literal["expired"] | t.Literal["valid"]
    session_available: bool
    trust_env: bool
    viessmann_api: ViessmannApiModel


class HealthModel(BaseModel):
    status: t.Literal["UP"]
    """
    Format is %d.%h.%m.%s.%m
    """
    uptime: str
    checks: ChecksModel


@router.get("/")
def health(response: Response, vicare: PyViCare = Depends(dependencies.get_vicare)) -> HealthModel:
    response.headers["Cache-Control"] = "no-cache"

    auth_token_status = (
        "invalid"
        if vicare.oauth_manager.oauth_session.token is None
        else "expired"
        if vicare.oauth_manager.oauth_session.token.is_expired()
        else "valid"
    )

    viessman_api_request_start_time = time.time()
    viessmann_api = {
        "online": vicare.oauth_manager.oauth_session.get("https://api.viessmann.com/iot", timeout=1).status_code == 200,
        "response_time_in_s": str(timedelta(seconds=time.time() - viessman_api_request_start_time)),
        "installations_found": len(vicare.installations) > 0,
    }

    uptime = str(timedelta(seconds=(time.time() - start_time)))

    return {
        "status": "UP",
        "uptime": uptime,
        "checks": {
            "auth_token": auth_token_status,
            "session_available": vicare.oauth_manager.oauth_session.session is not None,
            "trust_env": vicare.oauth_manager.oauth_session.trust_env,
            "viessmann_api": viessmann_api,
        },
    }
