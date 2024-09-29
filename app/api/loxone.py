import re

import requests
from fastapi import APIRouter, Depends, HTTPException
from requests.auth import HTTPBasicAuth
from starlette import status

from app import dependencies
from app.settings import Settings

ROUTE_PREFIX_LOXONE = "/loxone"
router = APIRouter(prefix=ROUTE_PREFIX_LOXONE)

CODE_PATTERN = re.compile(r'Code="(\d+)"')


@router.get("/mode/sleep/state", status_code=status.HTTP_200_OK)
def get_mode_sleep(settings: Settings = Depends(dependencies.get_settings)) -> bool:
    data = requests.get(
        f"{settings.loxone_url}/dev/sps/io/1b60daf4-0071-17ba-ffffed57184a04d2",
        auth=(HTTPBasicAuth(settings.loxone_user, settings.loxone_password)),
        verify=True,
    ).text

    if match := CODE_PATTERN.search(data):
        real_status_code = int(match.group(1))
        if real_status_code != 200:
            raise HTTPException(real_status_code, detail=f"Loxone answered with HTTP {real_status_code}")

    return True if 'value="1"' in data else False
