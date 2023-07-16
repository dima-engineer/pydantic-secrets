class PydanticSecretSourceWarning(Warning):
    def __init__(self, field_name: str):
        self.field_name = field_name


class SecretReceivingWarning(PydanticSecretSourceWarning):
    def __init__(self, field_name: str):
        self.field_name = field_name

    def __str__(self):
        msg = f'Couldn\'t load secret for field "{self.field_name}".'
        return msg


class SecretVersionNotSpecifiedWarning(PydanticSecretSourceWarning):
    def __str__(self):
        return f'There is no secret version specified for field "{self.field_name}". Skipping'
