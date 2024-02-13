from typing import Protocol


class SecretManagerClientProtocol(Protocol):
    def get_secret(self, secret_name: str, secret_version: str) -> str:
        """
        Returns a secret from secret manager by secret name and secret version
        :param secret_name: Name of secret to be fetched
        :param secret_version: Version of the secret to be fetched
        :return: Secret represented as a string
        """
