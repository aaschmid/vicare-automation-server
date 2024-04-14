from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    client_id: str
    email: str
    password: str

    loxone_url: str
    loxone_user: str
    loxone_password: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __hash__(self):
        """
        Custom hash function based on mail - one client per mail - to be able to hash it in
        order to cache dependent (sub-)services (e.g. using an `lru_cache`)

        :return: hashed concatenation of settings variables
        """
        return hash(self.client_id + self.email + self.password)
