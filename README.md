# pydantic-secrets
This library helps you to autoload your secrets into a
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
object from sources like Google Secret Manager or any other secret manager you want.

## Installation
Requires Python 3.11+.

```shell
pip install pydantic-secrets
```

or with [uv](https://docs.astral.sh/uv/):

```shell
uv add pydantic-secrets
```

## Usage
You can use the pydantic-secrets library in 2 scenarios:
* Use a ready-made `SecretManagerClient` provided by the library
* Implement a custom `SecretManagerClient` and use it in your `SecretManagerSource`

### Describing secrets in fields
Secrets are declared per field through `json_schema_extra`. The following keys are supported:

| Key                  | Description                                                                  |
|----------------------|------------------------------------------------------------------------------|
| `secret_name`        | Name of the secret in the secret manager.                                    |
| `secret_name_env`    | Name of an env variable holding the secret name. Overrides `secret_name`.    |
| `secret_version`     | Version of the secret.                                                       |
| `secret_version_env` | Name of an env variable holding the secret version. Overrides `secret_version`. |

If no version is set for a field, `default_secret_version` passed to `SecretManagerSource` is used.
If there is no version at all, the field is skipped with a `SecretVersionNotSpecifiedWarning`.
If the secret can't be fetched, a `SecretReceivingWarning` is emitted and the value is taken from other sources.

Nested models (like `db` below) are supported as well.

### Ready [`SecretManagerClient`](./pydantic_secrets/abstract.py)
Currently, the library provides only [`GoogleSecretManagerClient`](./pydantic_secrets/secret_manager/gcp.py)
out of the box.

Here is an example of usage:
```python
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

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
            "secret_version": "v2",
        },
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

    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="allow")


if __name__ == "__main__":
    load_dotenv()
    settings = Settings(_env_file="./.env", _env_file_encoding="utf-8")
    print(f"{settings=}")
```
Some important items here:
* You should either pass the `credentials` parameter to the `GoogleSecretManagerClient` or have the
[GOOGLE_APPLICATION_CREDENTIALS](https://cloud.google.com/docs/authentication/application-default-credentials#GAC)
env variable in place that points to the JSON file with credentials.
* If you want to understand better what happens here, please read
[this article](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#customise-settings-sources).
What we do is add a custom settings source represented by `SecretManagerSource`.
* Sources are listed in priority order, so in the example above values from init arguments, env variables
and `.env` file take precedence over secrets.

### Custom [`SecretManagerClient`](./pydantic_secrets/abstract.py)
To use any other secret manager, subclass `SecretManagerClientABC` and implement `get_secret`.
Any object with a matching `get_secret(secret_name, secret_version)` method works too
(see [`SecretManagerClientProtocol`](./pydantic_secrets/protocols.py)).

```python
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

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
    password: str = Field(
        json_schema_extra={
            "secret_name": "test-db-password",
            "secret_version": "v2",
        },
    )


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

    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="allow")


if __name__ == "__main__":
    load_dotenv()
    settings = Settings(_env_file="./.env", _env_file_encoding="utf-8")
    print(f"{settings=}")
```

## Development
The project uses [uv](https://docs.astral.sh/uv/) for dependency management and
[lets](https://lets-cli.org/) as a task runner.

```shell
uv sync --dev  # install dependencies
lets fmt       # format code and apply lint fixes (ruff)
lets val       # lint, check formatting (ruff) and type-check (pyright)
lets test      # run tests with coverage
```
