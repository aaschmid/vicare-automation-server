from ipaddress import IPv4Address

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    client_id: str
    email: str
    password: str

    appletv_host: IPv4Address
    appletv_companion_port: int
    appletv_companion_identifier: str
    appletv_companion_credentials: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __hash__(self):
        """
        Custom hash function based on mail - one client per mail - to be able to hash it in
        order to cache dependent (sub-)services (e.g. using an `lru_cache`)

        :return: hashed concatenation of settings variables
        """
        return hash(
            self.client_id
            + self.email
            + self.password
            + str(self.appletv_host)
            + str(self.appletv_companion_port)
            + self.appletv_companion_identifier
            + self.appletv_companion_credentials
        )
