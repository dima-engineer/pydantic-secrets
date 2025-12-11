import os

import pytest
from pydantic import ValidationError

from pydantic_secrets.exceptions import SecretManagerClientError
from snippets.google_secret_manager import Settings
from google.api_core.exceptions import GoogleAPIError
from unittest.mock import MagicMock


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


@pytest.fixture(autouse=True)
def mock_gcp_secret_manager_client(mocker):
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_payload = MagicMock()
    mock_data = MagicMock()
    
    mock_data.decode.return_value = "test-value-from-secret-manager"
    mock_payload.data = mock_data
    mock_response.payload = mock_payload
    mock_client_instance.access_secret_version.return_value = mock_response
    
    mock_class = mocker.patch("pydantic_secrets.secret_manager.gcp.SecretManagerServiceClient", return_value=mock_client_instance)
    return mock_client_instance

def test_settings_with_gcp_secret_manager__success():
    secret_manager_return_value = "test-value-from-secret-manager"
    settings = Settings()
    assert settings.db.host == os.getenv("DB__HOST")
    assert settings.db.name == os.getenv("DB__NAME")
    assert settings.db.user == os.getenv("DB__USER")
    assert settings.db.password == secret_manager_return_value
    assert settings.var1 == secret_manager_return_value
    assert settings.var2 == secret_manager_return_value


def test_settings_with_gcp_secret_manager__var2_no_secret_name_env():
    os.environ.pop("VAR2_SECRET_NAME")
    with pytest.raises(ValidationError) as e:
        Settings()
    pydantic_errors = e.value.errors()
    assert len(pydantic_errors) == 1
    assert pydantic_errors[0]["type"] == "missing"
    assert pydantic_errors[0]["loc"] == ("var2",)

def test_settings_with_gcp_secret_manager__google_api_error(mock_gcp_secret_manager_client):
    mock_gcp_secret_manager_client.access_secret_version.side_effect = GoogleAPIError("test-error")
    with pytest.raises(ValidationError) as e:
        Settings()