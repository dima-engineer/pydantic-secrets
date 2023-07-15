from google.api_core.exceptions import GoogleAPIError
from google.auth.credentials import Credentials
from google.cloud.secretmanager import SecretManagerServiceClient

from pydantic_secrets import SecretManagerClientABC
from pydantic_secrets.exceptions import SecretManagerClientError

DEFAULT_ENCODING_TYPE = "utf-8"


class GoogleSecretManagerClient(SecretManagerClientABC):
    _client: SecretManagerServiceClient

    def __init__(
        self,
        project_id: str,
        credentials: Credentials | None = None,
        encoding_type: str = DEFAULT_ENCODING_TYPE,
    ):
        self.project_id = project_id
        self._client_credentials = credentials
        self._secret_path_template = f"projects/{self.project_id}" + "/secrets/{secret_name}/versions/{secret_version}"
        self._encoding_type = DEFAULT_ENCODING_TYPE

    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = SecretManagerServiceClient(credentials=self._client_credentials)
        return self._client

    def get_secret(self, secret_name: str, secret_version: str) -> str:
        try:
            response = self.client.access_secret_version(  # pyright: ignore [reportUnknownMemberType]
                name=self._secret_path_template.format(secret_name=secret_name, secret_version=secret_version)
            )
        except GoogleAPIError as e:
            raise SecretManagerClientError(
                f'Error during getting "{secret_name}" from the Google Secret Manager'
            ) from e
        payload = response.payload.data.decode(self._encoding_type)
        return payload
