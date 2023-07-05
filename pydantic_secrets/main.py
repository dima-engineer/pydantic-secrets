import os
import typing as t
import warnings
from typing import Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from pydantic_secrets.protocols import SecretManagerClientProtocol

from .warnings import SecretReceivingWarning, SecretVersionNotSpecifiedWarning

EXTRA_SECRET_NAME_KEY = "secret_name"
ENV_SECRET_NAME_KEY = "secret_name_env"
EXTRA_SECRET_VERSION_KEY = "secret_version"
ENV_SECRET_VERSION_KEY = "secret_version_env"


class SecretManagerSource(PydanticBaseSettingsSource):
    def __init__(
        self,
        settings_cls: type[BaseSettings],
        secret_manager_client: SecretManagerClientProtocol,
        default_secret_version: str | None = None,
    ):
        super().__init__(settings_cls)
        self.__secret_manager__ = secret_manager_client
        self.__default_secret_version__ = default_secret_version

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        return field_name, field.default, self.field_is_complex(field)

    def __call__(self) -> dict[str, Any]:
        return self._process_fields(self.settings_cls.model_fields)

    def _get_secret_info_from_extra(
        self,
        extra: dict[str, t.Any],
    ) -> tuple[str | None, str | None]:
        secret_name = extra.get(EXTRA_SECRET_NAME_KEY)
        secret_name_env = extra.get(ENV_SECRET_NAME_KEY)
        if secret_name_env:
            secret_name = os.getenv(secret_name_env) or secret_name
        secret_version = extra.get(EXTRA_SECRET_VERSION_KEY)
        secret_version_env = extra.get(ENV_SECRET_VERSION_KEY)
        if secret_version_env:
            secret_version = os.getenv(secret_version_env) or secret_version
        secret_version = secret_version or self.__default_secret_version__
        return secret_name, secret_version

    def _process_fields(self, fields: dict[str, FieldInfo]):
        d: dict[str, t.Any] = {}
        for field_name, field in fields.items():
            if self.field_is_complex(field):
                if field.annotation and issubclass(field.annotation, BaseModel):
                    d[field_name] = self._process_fields(field.annotation.model_fields)
                    continue
                d[field_name] = field
                continue
            secret_name, secret_version = (
                self._get_secret_info_from_extra(field.json_schema_extra)
                if field.json_schema_extra
                else (None, None)
            )
            if secret_name and secret_version:
                try:
                    d[field_name] = self.__secret_manager__.get_secret(
                        secret_name=secret_name,
                        secret_version=secret_version,
                    )
                except Exception:
                    warnings.warn(field_name, category=SecretReceivingWarning)
                    pass
            elif secret_name and not secret_version:
                warnings.warn(field_name, category=SecretVersionNotSpecifiedWarning)
        return d
