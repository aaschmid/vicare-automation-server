from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from PyViCare.PyViCare import PyViCare

from app.settings import Settings


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_vicare(settings: Annotated[Settings, Depends(get_settings)]) -> PyViCare:
    vicare = PyViCare()
    vicare.setCacheDuration(60)
    vicare.initWithCredentials(settings.email, settings.password, settings.client_id, "vicare.token")
    return vicare
