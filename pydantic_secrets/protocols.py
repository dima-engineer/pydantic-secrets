from typing import Protocol


class SecretManagerClientProtocol(Protocol):
    def get_secret(self, secret_name: str, secret_version: str) -> str:
        ...
