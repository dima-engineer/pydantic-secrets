import typing as t
import os
from pydantic import Field, BaseModel
from pydantic.v1.env_settings import SettingsSourceCallable
from pydantic_settings import BaseSettings

from pydantic_secrets.protocols import SecretManagerProtocol


class SecretManagerConfig:

    __secret_manager__: SecretManagerProtocol

    @classmethod
    def _get_secret_info_from_extra(
        cls, extra: dict[str, t.Any]
    ) -> tuple[str | None, str | None]:
        secret_name = extra.get("secret_name")
        secret_name_env = extra.get("secret_name_env")
        if secret_name_env:
            secret_name = os.getenv(secret_name_env) or secret_name
        secret_version = extra.get("secret_version")
        secret_version_env = extra.get("secret_version_env")
        if secret_version_env:
            secret_version = os.getenv(secret_version_env) or secret_version
        secret_version = secret_version or "latest"
        return secret_name, secret_version

    @classmethod
    def _process_fields(cls, fields: dict[str, Field]):
        d: dict[str, t.Any] = {}
        for field_name, field in fields.items():
            if field.is_complex():
                if issubclass(field.type_, BaseModel):
                    d[field_name] = cls._process_fields(field.type_.model_fields)
                    continue
                d[field_name] = field
                continue
            secret_name, secret_version = cls._get_secret_info_from_extra(
                field.field_info.extra
            )
            if secret_name and secret_version:
                try:
                    d[field_name] = cls.__secret_manager__.get_secret(
                        secret_name=secret_name,
                        secret_version=secret_version,
                    )
                except Exception:
                    pass
        return d

    @classmethod
    def get_secrets(cls, settings: BaseSettings) -> dict[str, str]:
        return cls._process_fields(settings.model_fields)

    @classmethod
    def customise_sources(
        cls,
        init_settings: SettingsSourceCallable,
        env_settings: SettingsSourceCallable,
        file_secret_settings: SettingsSourceCallable,
    ):
        return (
            init_settings,
            env_settings,
            file_secret_settings,
            cls.get_secrets,
        )
