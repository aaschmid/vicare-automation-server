from functools import lru_cache
from typing import Annotated

from fastapi import Depends
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
