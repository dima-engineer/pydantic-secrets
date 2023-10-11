class PydanticSecretsError(Exception):
    pass


class SecretManagerClientError(PydanticSecretsError):
    pass
