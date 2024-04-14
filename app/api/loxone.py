import re
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException, Path
from requests.auth import HTTPBasicAuth
from starlette import status

from app import dependencies
from app.settings import Settings

ROUTE_PREFIX_LOXONE = "/loxone"
router = APIRouter(prefix=ROUTE_PREFIX_LOXONE)

CODE_PATTERN = re.compile(r'Code="(\d+)"')


# Not really restful but required for Mikrotik's netwatch HTTP probe, see https://help.mikrotik.com/docs/display/ROS/Netwatch
@router.get("/mode/sleep/{state}", status_code=status.HTTP_204_NO_CONTENT)
def get_mode_sleep(
    state: Annotated[str, Path(title="The state for which a HTTP-200 should be answered", pattern=r"^on|off$")],
    settings: Settings = Depends(dependencies.get_settings),
) -> None:
    data = requests.get(
        f"{settings.loxone_url}/dev/sps/io/1b60daf4-0071-17ba-ffffed57184a04d2",
        auth=(HTTPBasicAuth(settings.loxone_user, settings.loxone_password)),
        verify=True,
    ).text

    if match := CODE_PATTERN.search(data):
        real_status_code = int(match.group(1))
        if real_status_code != 200:
            raise HTTPException(real_status_code, detail=f"Loxone answered with HTTP {real_status_code}")

    if f'value="{0 if state == "off" else 1}"' in data:
        return None

    raise HTTPException(status.HTTP_404_NOT_FOUND)
