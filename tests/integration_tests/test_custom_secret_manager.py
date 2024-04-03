import os

import pytest
from pydantic import ValidationError

from snippets.custom_secret_manager_implementation import Settings

ENV_VARIABLES = {
    "DB__HOST": "test-db-host",
    "DB__NAME": "test-db-name",
    "DB__USER": "test-db-user",
    "VAR1_SECRET_VERSION": "v5",
    "VAR2_SECRET_NAME": "test-var2-secret-name",
}


@pytest.fixture(autouse=True)
def pre_setup_env_vars():
    for env_var_name, env_var_value in ENV_VARIABLES.items():
        os.environ[env_var_name] = env_var_value
    yield
    for env_var_key in ENV_VARIABLES:
        os.environ.pop(env_var_key, None)


def test_settings_with_custom_secret_manager__success():
    secret_manager_return_value = "test-value-from-secret-manager"
    settings = Settings()
    assert settings.db.host == os.getenv("DB__HOST")
    assert settings.db.name == os.getenv("DB__NAME")
    assert settings.db.user == os.getenv("DB__USER")
    assert settings.db.password == secret_manager_return_value
    assert settings.var1 == secret_manager_return_value
    assert settings.var2 == secret_manager_return_value


def test_settings_with_custom_secret_manager__var2_no_secret_name_env():
    os.environ.pop("VAR2_SECRET_NAME")
    with pytest.raises(ValidationError) as e:
        Settings()
    pydantic_errors = e.value.errors()
    assert len(pydantic_errors) == 1
    assert pydantic_errors[0]["type"] == "missing"
    assert pydantic_errors[0]["loc"] == ("var2",)
