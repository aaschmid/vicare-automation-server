import os
import tempfile
from ipaddress import IPv4Address
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
    appletv_host = "192.168.1.100"
    appletv_companion_port = "49153"
    appletv_companion_identifier = "AA:BB:CC:DD:EE:FF"
    appletv_companion_credentials = "creds123"

    with Path(".env").open("w") as f:
        f.write(f"""\
            CLIENT_ID="{client_id}"
            EMAIL="{email}"
            PASSWORD="{password}"
            APPLETV_HOST="{appletv_host}"
            APPLETV_COMPANION_PORT="{appletv_companion_port}"
            APPLETV_COMPANION_IDENTIFIER="{appletv_companion_identifier}"
            APPLETV_COMPANION_CREDENTIALS="{appletv_companion_credentials}"
        """.strip())

    settings = Settings()

    assert settings.client_id == client_id
    assert settings.email == email
    assert settings.password == password
    assert settings.appletv_host == IPv4Address(appletv_host)
    assert settings.appletv_companion_port == int(appletv_companion_port)
    assert settings.appletv_companion_identifier == appletv_companion_identifier
    assert settings.appletv_companion_credentials == appletv_companion_credentials


def test_init_settings_using_env_variables() -> None:
    client_id = "environment variable"
    email = "test2@example.com"
    password = "654321"
    appletv_host = "192.168.1.200"
    appletv_companion_port = "49154"
    appletv_companion_identifier = "11:22:33:44:55:66"
    appletv_companion_credentials = "creds456"
    prepare_env_variables(
        client_id,
        email,
        password,
        appletv_host,
        appletv_companion_port,
        appletv_companion_identifier,
        appletv_companion_credentials,
    )

    settings = Settings()

    assert settings.client_id == client_id
    assert settings.email == email
    assert settings.password == password
    assert settings.appletv_host == IPv4Address(appletv_host)
    assert settings.appletv_companion_port == int(appletv_companion_port)
    assert settings.appletv_companion_identifier == appletv_companion_identifier
    assert settings.appletv_companion_credentials == appletv_companion_credentials


def test_hash_return_same_for_same_config() -> None:
    client_id = "environment variable"
    email = "test2@example.com"
    password = "654321"
    appletv_host = "192.168.1.50"
    appletv_companion_port = "49153"
    appletv_companion_identifier = "AA:BB:CC:DD:EE:FF"
    appletv_companion_credentials = "creds789"

    prepare_env_variables(
        client_id,
        email,
        password,
        appletv_host,
        appletv_companion_port,
        appletv_companion_identifier,
        appletv_companion_credentials,
    )
    settings1 = Settings()
    settings2 = Settings()

    assert hash(settings1) == hash(settings2)


def test_hash_return_different_for_different_config() -> None:
    email = "test2@example.com"
    password = "654321"
    appletv_host = "192.168.1.50"
    appletv_companion_port = "49153"
    appletv_companion_identifier = "AA:BB:CC:DD:EE:FF"
    appletv_companion_credentials = "creds789"

    prepare_env_variables(
        "env_var_1",
        email,
        password,
        appletv_host,
        appletv_companion_port,
        appletv_companion_identifier,
        appletv_companion_credentials,
    )
    settings1 = Settings()

    prepare_env_variables(
        "env_var_2",
        email,
        password,
        appletv_host,
        appletv_companion_port,
        appletv_companion_identifier,
        appletv_companion_credentials,
    )
    settings2 = Settings()

    assert hash(settings1) != hash(settings2)


def test_hash_return_different_for_different_appletv_config() -> None:
    client_id = "same_client"
    email = "same@example.com"
    password = "same_pass"
    appletv_host = "192.168.1.50"
    appletv_companion_port = "49153"
    appletv_companion_identifier = "id1"

    prepare_env_variables(
        client_id,
        email,
        password,
        appletv_host,
        appletv_companion_port,
        appletv_companion_identifier,
        "creds1",
    )
    settings1 = Settings()

    prepare_env_variables(
        client_id,
        email,
        password,
        appletv_host,
        appletv_companion_port,
        appletv_companion_identifier,
        "creds2",
    )
    settings2 = Settings()

    assert hash(settings1) != hash(settings2)


def prepare_env_variables(
    client_id: str,
    email: str,
    password: str,
    appletv_host: str,
    appletv_companion_port: str,
    appletv_companion_identifier: str,
    appletv_companion_credentials: str,
) -> None:
    os.environ["CLIENT_ID"] = client_id
    os.environ["EMAIL"] = email
    os.environ["PASSWORD"] = password
    os.environ["APPLETV_HOST"] = appletv_host
    os.environ["APPLETV_COMPANION_PORT"] = appletv_companion_port
    os.environ["APPLETV_COMPANION_IDENTIFIER"] = appletv_companion_identifier
    os.environ["APPLETV_COMPANION_CREDENTIALS"] = appletv_companion_credentials
