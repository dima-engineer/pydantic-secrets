from abc import ABC, abstractmethod


class SecretManagerClientABC(ABC):
    @abstractmethod
    def get_secret(self, secret_name: str, secret_version: str) -> str:
        ...
