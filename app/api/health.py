import time
import typing as t
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from PyViCare.PyViCare import PyViCare
from starlette import status

from app import dependencies
from app.request_tracking import LastFailureMessage, RequestTracker

# TODO maybe use basic auth? configured?
start_time = time.time()

ROUTE_PREFIX_HEALTH = "/health"


# Failure expiration time: 15 minutes in seconds
FAILURE_EXPIRATION_SECONDS = 15 * 60


router = APIRouter(prefix=ROUTE_PREFIX_HEALTH)


AuthTokenStatus = t.Literal["invalid", "expired", "valid"]


class ChecksModel(BaseModel):
    auth_token: AuthTokenStatus
    no_of_installations: int
    session_available: bool
    trust_env: bool


class LastFailureModel(BaseModel):
    endpoint: str
    message: str | None
    status_code: int
    timestamp: str


class RequestsModel(BaseModel):
    request_stats: dict[str, t.Any]
    last_failure_message: LastFailureModel | None


class HealthModel(BaseModel):
    status: t.Literal["UP"]
    """
    Numeric status code (1-10):
    - 1: Online
    - 2-8: Error types
    - 9-10: Reserved
    """
    status_code: int
    """
    Format is %d.%h.%m.%s.%m
    """
    uptime: str
    checks: ChecksModel
    requests: RequestsModel


@router.get("")
def health(
    response: Response,
    vicare: Annotated[PyViCare, Depends(dependencies.get_vicare)],
    request_tracker: Annotated[RequestTracker, Depends(dependencies.get_request_tracker)],
) -> HealthModel:
    response.headers["Cache-Control"] = "no-cache"

    auth_token_status: AuthTokenStatus = (
        "invalid"
        if vicare.oauth_manager.oauth_session.token is None
        else "expired" if vicare.oauth_manager.oauth_session.token.is_expired() else "valid"
    )

    uptime = str(timedelta(seconds=(time.time() - start_time)))

    last_failure = request_tracker.get_last_failure_message()
    last_failure_model = (
        None
        if not last_failure
        else LastFailureModel(
            endpoint=last_failure["endpoint"],
            message=last_failure["message"],
            status_code=last_failure["status_code"],
            timestamp=datetime.fromtimestamp(last_failure["timestamp"]).isoformat(),
        )
    )

    return HealthModel(
        status="UP",
        status_code=_get_error_status_code(auth_token_status, last_failure),
        uptime=uptime,
        checks=ChecksModel(
            auth_token=auth_token_status,
            no_of_installations=len(vicare.installations),
            session_available=vicare.oauth_manager.oauth_session.session is not None,
            trust_env=vicare.oauth_manager.oauth_session.trust_env,
        ),
        requests=RequestsModel(
            request_stats=request_tracker.get_statistics(),
            last_failure_message=last_failure_model,
        ),
    )


def _get_error_status_code(auth_token_status: str, last_failure_message: LastFailureMessage | None) -> int:
    """
    Determine numeric status code (1-10) based on last failure.

    Failures older than 15 minutes are ignored for status code calculation but still returned in the response.

    Status codes:
    - 1: Online (no failures or failures older than 15 minutes)
    - 2: Invalid authentication token
    - 3: Authentication Error (401)
    - 4: Rate Limit Error (429)
    - 5: Invalid Configuration Error (424)
    - 6: Not Supported/Invalid Data/Command Error (405)
    - 7: Internal Server Error (500)
    - 8: Uncategorized Error
    - 9-10: Reserved for future error types
    """
    if auth_token_status == "invalid":
        return 2
    if not last_failure_message:
        return 1

    failure_age = time.time() - last_failure_message["timestamp"]
    if failure_age > FAILURE_EXPIRATION_SECONDS:
        return 1

    failure_status_code = last_failure_message["status_code"]
    if failure_status_code == status.HTTP_401_UNAUTHORIZED:
        return 3
    elif failure_status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return 4
    elif failure_status_code == status.HTTP_424_FAILED_DEPENDENCY:
        return 5
    elif failure_status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return 6
    elif failure_status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        return 7
    else:
        return 8
