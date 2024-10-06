from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth
from starlette import status

from app.api.loxone import ROUTE_PREFIX_LOXONE
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_get_mode_wifi_invalid_state(dependency_mocker):
    response = client.get(f"{ROUTE_PREFIX_LOXONE}/mode/wifi/invalid")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "dependency_mocker",
    [[app, {"loxone_url": "https://localhost:8080", "loxone_user": "reader", "loxone_password": "password1"}]],
    indirect=True,
)
def test_get_mode_wifi_should_call_correct_api(dependency_mocker, mocker):
    mock = mocker.patch("app.api.loxone.requests.get", return_value=(Mock(text='<LL Code="200"/>')))

    client.get(f"{ROUTE_PREFIX_LOXONE}/mode/wifi/state")

    assert mock.call_count == 1
    assert mock.call_args.args[0] == "https://localhost:8080/dev/sps/io/1da6432d-00ed-6dfa-ffffed57184a04d2"
    assert mock.call_args.kwargs["auth"] == HTTPBasicAuth("reader", "password1")
    assert mock.call_args.kwargs["verify"]


@pytest.mark.parametrize("dependency_mocker", [app], indirect=True)
def test_get_mode_wifi_should_forward_non_200_from_loxone(dependency_mocker, mocker):
    mocker.patch("app.api.loxone.requests.get", return_value=(Mock(text='<LL control="foobar" value="0" Code="403"/>')))

    response = client.get(f"{ROUTE_PREFIX_LOXONE}/mode/wifi/state")

    assert response.status_code == 403


@pytest.mark.parametrize(
    "dependency_mocker, value, expected_json, expected_str",
    [
        (app, 0, False, "false"),
        (app, 1, True, "true"),
    ],
    indirect=["dependency_mocker"],
)
def test_get_mode_wifi(dependency_mocker, mocker, value, expected_json, expected_str):
    mocker.patch(
        "app.api.loxone.requests.get", return_value=(Mock(text=f'<LL control="foobar" value="{value}" Code="200"/>'))
    )

    response = client.get(f"{ROUTE_PREFIX_LOXONE}/mode/wifi/state")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_json
    assert response.text == expected_str
