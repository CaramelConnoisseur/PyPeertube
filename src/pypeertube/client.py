"""A client to talk to Peertube"""

from enum import Enum

from requests import get, post, Session

from . import __version__


class AuthEndpoints(Enum):
    """Endpoints for managing authentication to Peertube."""

    OAUTH_CLIENT = "api/v1/oauth-clients/local"
    """Login prerequisite"""

    LOGIN = "api/v1/users/token"
    """Login"""

    LOGOUT = "api/v1/users/revoke-token"
    """Logout"""


class ApiClient:
    """A client to talk to Peertube"""

    _base_url: str
    _username: str
    _password: str
    _access_token: str
    _session: Session

    def __init__(self, base_url: str, username: str, password: str):

        if not base_url.endswith("/"):
            base_url = base_url + "/"

        oauth_response = get(base_url + AuthEndpoints.OAUTH_CLIENT.value, timeout=3)
        oauth_response.raise_for_status()
        oauth = oauth_response.json()

        auth_response = post(
            base_url + AuthEndpoints.LOGIN.value,
            data={
                "client_id": oauth["client_id"],
                "client_secret": oauth["client_secret"],
                "grant_type": "password",
                "username": username,
                "password": password,
            },
            timeout=3,
        )
        auth_response.raise_for_status()

        self._base_url = base_url
        self._username = username
        self._password = password
        self._access_token = auth_response.json()["access_token"]
        self._session = Session()
        self._session.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": "Mozilla/5.0 +https://github.com/CaramelConnoisseur/peertube-python "
            f"Peertube-Python/{__version__}",
        }

    @property
    def base_url(self) -> str:
        """The base URL of the Peertube instance."""
        return self._base_url

    @property
    def username(self) -> str:
        """The authenticated username."""
        return self._username

    @property
    def session(self) -> Session:
        """A requests.Session configured with the required authentication header."""
        return self._session

    def logout(self) -> bool:
        """Revoke an access token.

        Args:
            access_token (str): The access token to revoke.

        Returns:
            bool: Whether the token was invalided.
        """

        self._session.close()
        resp = post(
            self._base_url + AuthEndpoints.LOGOUT.value,
            headers={"Authorization": f"Bearer {self._access_token}"},
            timeout=3,
        )
        return resp.json()["success"]
