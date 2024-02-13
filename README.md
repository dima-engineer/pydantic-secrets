# pydantic-secrets
This library helps you to autoload your secrets into 
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) 
object from sources like Google Secret Manager, AWS Secret Manager or whatever you want.

## Usage
You can use pydantic-secrets lib in 2 scenarios:
* Use a ready `SecretManagerClient` library provides
* Implement a custom `SecretManagerClient` and use it in your SecretSource

### Ready [`SecretManagerClient`](./pydantic_secrets/abstract.py)
Currently, the library provides only [`GoogleSecretManagerClient`](./pydantic_secrets/secret_manager/gcp.py)
out of the box. 

There is an example of usage:
```python
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from pydantic_secrets import SecretManagerSource
from pydantic_secrets.secret_manager import GoogleSecretManagerClient


class DatabaseSettings(BaseModel):
    name: str
    host: str
    user: str
    port: int = 3306
    password: str = Field(
        json_schema_extra={
            "secret_name": "test-db-password",
            "secret_version": "v2"
        }
    )


class Settings(BaseSettings):
    var1: str = Field(json_schema_extra={"secret_name": "test-secret"})
    var2: str = Field(json_schema_extra={"secret_name_env": "VAR2_SECRET_NAME"})
    db: DatabaseSettings

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
                secret_manager_client=GoogleSecretManagerClient(
                    project_id="test-project",
                ),
                default_secret_version="latest",
            ),
        )

    class Config:
        env_nested_delimiter = "__"
        extra = "allow"


if __name__ == "__main__":
    load_dotenv()
    settings = Settings(_env_file="./.env", _env_file_encoding="utf-8")
    print(f"{settings=}")
```
Some important items here:
* You should either pass `credentials` parameter to the `GoogleSecretManagerClient` or have
[GOOGLE_APPLICATION_CREDENTIALS](https://cloud.google.com/docs/authentication/application-default-credentials#GAC) env variable in place that points on the JSON file with 
credentials. 
* If you want to understand more what happens here, please read 
[this article](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#customise-settings-sources).
What we do, is actually adding a custom settings source represented by `SecretManagerSource`
 ### Custom [`SecretManagerClient`](./pydantic_secrets/abstract.py)

```python
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from pydantic_secrets import SecretManagerClientABC, SecretManagerSource


class CustomSecretManagerExample(SecretManagerClientABC):
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
    var1: str = Field(json_schema_extra={"secret_name": "test-secret"})
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
                secret_manager_client=CustomSecretManagerExample(),
                default_secret_version="latest",
            ),
        )

    class Config:
        env_nested_delimiter = "__"
        extra = "allow"


if __name__ == "__main__":
    load_dotenv()
    settings = Settings(_env_file="./.env", _env_file_encoding="utf-8")
    print(f"{settings=}")
```
