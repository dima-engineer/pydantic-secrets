from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from pydantic_secrets import SecretManagerClientABC, SecretManagerSource


class SecretManagerExample(SecretManagerClientABC):
    def get_secret(self, secret_name: str, secret_version: str) -> str:
        print(f'Getting secret "{secret_name}:{secret_version}"')
        return "test-value-from-secret-manager"


class SomeEnum(BaseModel):
    variable1: tuple[str, str] = ("foo", "bar")


class DatabaseSettings(BaseModel):
    name: str
    host: str
    user: str
    port: int = 3306
    password: str = Field(json_schema_extra={"secret_name": "test-db-password", "secret_version": "v2"})


class Settings(BaseSettings):
    var1: str = Field(json_schema_extra={"secret_name": "test-secret", "secret_version_env": "VAR1_SECRET_VERSION"})
    var2: str = Field(json_schema_extra={"secret_name_env": "VAR2_SECRET_NAME"})
    db: DatabaseSettings
    some_enum: SomeEnum

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            SecretManagerSource(
                settings_cls,
                secret_manager_client=SecretManagerExample(),
                default_secret_version="latest",
            ),
        )

    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="allow")


if __name__ == "__main__":
    load_dotenv()
    settings = Settings(_env_file="./.env", _env_file_encoding="utf-8")
    print(f"{settings=}")
