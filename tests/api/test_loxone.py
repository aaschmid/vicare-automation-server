from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth
from starlette import status

from app.api.loxone import ROUTE_PREFIX_LOXONE
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_get_mode_sleep_invalid_state(dependency_mocker):
    response = client.get(f"{ROUTE_PREFIX_LOXONE}/mode/sleep/invalid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "dependency_mocker",
    [[app, {"loxone_url": "https://localhost:8080", "loxone_user": "reader", "loxone_password": "password1"}]],
    indirect=True,
)
def test_get_mode_sleep_should_call_correct_api(dependency_mocker, mocker):
    mock = mocker.patch("app.api.loxone.requests.get", return_value=(Mock(text='<LL Code="200"/>')))

    client.get(f"{ROUTE_PREFIX_LOXONE}/mode/sleep/on")

    assert mock.call_count == 1
    assert mock.call_args.args[0] == "https://localhost:8080/dev/sps/io/1b60daf4-0071-17ba-ffffed57184a04d2"
    assert mock.call_args.kwargs["auth"] == HTTPBasicAuth("reader", "password1")
    assert mock.call_args.kwargs["verify"]


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_get_mode_sleep_should_forward_non_200_from_loxone(dependency_mocker, mocker):
    mocker.patch("app.api.loxone.requests.get", return_value=(Mock(text='<LL control="foobar" value="0" Code="403"/>')))

    response = client.get(f"{ROUTE_PREFIX_LOXONE}/mode/sleep/off")

    assert response.status_code == 403


@pytest.mark.parametrize(
    "dependency_mocker, state, value, expected",
    [
        (app, "on", 0, status.HTTP_404_NOT_FOUND),
        (app, "on", 1, status.HTTP_204_NO_CONTENT),
        (app, "off", 0, status.HTTP_204_NO_CONTENT),
        (app, "off", 1, status.HTTP_404_NOT_FOUND),
    ],
    indirect=["dependency_mocker"],
)
def test_get_mode_sleep(dependency_mocker, mocker, state, value, expected):
    mocker.patch(
        "app.api.loxone.requests.get", return_value=(Mock(text=f'<LL control="foobar" value="{value}" Code="200"/>'))
    )

    response = client.get(f"{ROUTE_PREFIX_LOXONE}/mode/sleep/{state}")

    assert response.status_code == expected
