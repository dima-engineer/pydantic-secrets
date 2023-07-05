from typing import Protocol


class SecretManagerProtocol(Protocol):

    def get_secret(self, secret_name: str, secret_version: str):
        ...
