"""Generic exceptions for Peertube."""

from requests import Response
from requests.exceptions import JSONDecodeError


class PeertubeError(Exception):
    """A generic Peertube error."""


class PeerTubeAPIBadResponseError(PeertubeError):
    """An unexpected API response was received."""


def raise_api_bad_response_error(response: Response):
    """Raise a PeerTubeAPIBadResponseError for the given response, trying to decode JSON response.

    Args:
        response (Response): The response to raise the error for.
    """

    try:
        raise PeerTubeAPIBadResponseError(
            response.url, response.status_code, response.reason, response.json()
        )
    except JSONDecodeError as e:
        raise PeerTubeAPIBadResponseError(
            response.url,
            response.status_code,
            response.reason,
            response.content.decode(),
        ) from e
