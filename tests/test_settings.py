import os
import tempfile
from pathlib import Path

import pytest

from app.settings import Settings


@pytest.fixture
def change_test_dir(request) -> None:
    temp_dir = tempfile.TemporaryDirectory(prefix="test_env")
    os.chdir(temp_dir.name)
    yield
    os.chdir(request.config.invocation_params.dir)


def test_init_settings_using_env_file(change_test_dir) -> None:
    client_id = ".env file"
    email = "test1@example.com"
    password = "123456"
    with Path.open(".env", "w") as f:
        f.write(
            f"""\
            CLIENT_ID="{client_id}"
            EMAIL="{email}"
            PASSWORD="{password}"
        """.strip()
        )

    settings = Settings()

    assert settings.client_id == client_id
    assert settings.email == email
    assert settings.password == password


def test_init_settings_using_env_variables() -> None:
    client_id = "environment variable"
    email = "test2@example.com"
    password = "654321"
    prepare_env_variables(client_id, email, password)

    settings = Settings()

    assert settings.client_id == client_id
    assert settings.email == email
    assert settings.password == password


def test_hash_return_same_for_same_config() -> None:
    client_id = "environment variable"
    email = "test2@example.com"
    password = "654321"

    prepare_env_variables(client_id, email, password)
    settings1 = Settings()
    settings2 = Settings()

    assert hash(settings1) == hash(settings2)


def test_hash_return_different_for_different_config() -> None:
    email = "test2@example.com"
    password = "654321"

    prepare_env_variables("env_var_1", email, password)
    settings1 = Settings()

    prepare_env_variables("env_var_2", email, password)
    settings2 = Settings()

    assert hash(settings1) != hash(settings2)


def prepare_env_variables(client_id: str, email: str, password: str) -> None:
    os.environ["CLIENT_ID"] = client_id
    os.environ["EMAIL"] = email
    os.environ["PASSWORD"] = password
