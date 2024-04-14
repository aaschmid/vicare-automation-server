from collections import namedtuple
from typing import Dict
from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import SubRequest
from fastapi import FastAPI
from PyViCare import PyViCare

from app.dependencies import get_settings, get_vicare


def check_args(args) -> (FastAPI, Dict):
    assert type(args) is FastAPI or (
        len(args) > 0 and type(args[0]) is FastAPI
    ), "First or only argument of `dependency_mocker` must be `app: FastAPI`"

    setting_values = {}
    if type(args) is FastAPI:
        app = args

    else:
        app = args[0]
        if len(args) > 1:
            assert isinstance(args[1], dict)
            setting_values = args[1]

    return app, setting_values


@pytest.fixture
def dependency_mocker(request: SubRequest) -> MagicMock:
    app, setting_values = check_args(request.param)

    settings = {
        "email": "test@example.com",
        "password": "password",
        "client_id": "test_client",
        "loxone_url": "http://127.0.0.1",
        "loxone_user": "user",
        "loxone_password": "password",
        **setting_values,
    }
    app.dependency_overrides[get_settings] = lambda: namedtuple("Settings", settings.keys())(*settings.values())

    vicare: PyViCare = MagicMock()
    app.dependency_overrides[get_vicare] = lambda: vicare

    return vicare
