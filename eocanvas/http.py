"""HTTP functions. Inspired by EUMDAC request module."""

from typing import Any, Dict

import requests
from requests.adapters import HTTPAdapter, Retry

from .exceptions import HTTPError, QuotaExceededError
from .logging import logger


def get_adapter(max_retries: int, backoff_factor: float) -> HTTPAdapter:
    """
    Returns an HTTPAdapter able to handling retries.
    See: https://requests.readthedocs.io/en/latest/user/advanced/#example-automatic-retries

    :param max_retries: Max number of retries before failing
    :type max_retries: int
    :param backoff_factor: A backoff factor to apply between attempts after the second try
    :type backoff_factor: float
    """
    retries = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    )
    return HTTPAdapter(max_retries=retries)


def request(
    method: str,
    url: str,
    max_retries: int = 5,
    backoff_factor: float = 0.25,
    **kwargs: Any,
) -> requests.Response:
    adapter = get_adapter(max_retries, backoff_factor)
    session = requests.Session()
    session.mount("https://", adapter)

    response = requests.Response()

    try:
        if hasattr(session, method):
            logger.debug(_pretty_print(method, url, kwargs))
            response = getattr(session, method.lower())(url, **kwargs)
            if response.status_code == 429:
                msg = response.json()["message"]
                raise QuotaExceededError(msg)
            response.raise_for_status()
        else:
            raise HTTPError(f"Operation not supported: {method}")
    except requests.exceptions.RetryError:
        raise HTTPError(f"Maximum retries ({max_retries}) reached for {method.capitalize()} {url}")

    return response


def get(url: str, **kwargs: Any) -> requests.Response:
    """Perform a GET HTTP request to the given `url` with the given parameters.

    Retries will be managed in a transparent way when making the request.

    :param url: URL to make the request to
    :type url: str

    :param kwargs: Extra arguments to pass to the request, refer to the requests library
        documentation for a list of possible arguments.
    :type kwargs: dict, optional

    :return: Response received from the server
    :rtype: requests.Response
    """
    return request("get", url, **kwargs)


def post(url: str, **kwargs: Any) -> requests.Response:
    """Perform a POST HTTP request to the given `url` with the given parameters.

    Retries and throttling will be managed in a transparent way when making the request.

    :param url: URL to make the request to
    :type url: str

    :param kwargs: Extra arguments to pass to the request, refer to the requests library
        documentation for a list of possible arguments.
    :type kwargs: dict, optional

    :return: Response received from the server
    :rtype: requests.Response
    """
    return request("post", url, **kwargs)


def patch(url: str, **kwargs: Any) -> requests.Response:
    """Perform a PATCH HTTP request to the given `url` with the given parameters.

    Retries and throttling will be managed in a transparent way when making the request.

    :param url: URL to make the request to
    :type url: str

    :param kwargs: Extra arguments to pass to the request, refer to the requests library
        documentation for a list of possible arguments.
    :type kwargs: dict, optional

    :return: Response received from the server
    :rtype: requests.Response
    """
    return request("patch", url, **kwargs)


def put(url: str, **kwargs: Any) -> requests.Response:
    """Perform a PUT HTTP request to the given `url` with the given parameters.

    Retries and throttling will be managed in a transparent way when making the request.

    :param url: URL to make the request to
    :type url: str

    :param kwargs: Extra arguments to pass to the request, refer to the requests library
        documentation for a list of possible arguments.
    :type kwargs: dict, optional

    :return: Response received from the server
    :rtype: requests.Response
    """
    return request("put", url, **kwargs)


def delete(url: str, **kwargs: Any) -> requests.Response:
    """Perform a DELETE HTTP request to the given `url` with the given parameters.

    Retries and throttling will be managed in a transparent way when making the request.

    :param url: URL to make the request to
    :type url: str

    :param kwargs: Extra arguments to pass to the request, refer to the requests library
        documentation for a list of possible arguments.
    :type kwargs: dict, optional

    :return: Response received from the server
    :rtype: requests.Response
    """
    return request("delete", url, **kwargs)


def _pretty_print(method: str, url: str, kwargs: Dict[str, Any]) -> str:
    """Returns a readable str of the given request."""
    pargs = {}
    for key in kwargs.keys():
        if key == "headers":
            headers = {
                header: kwargs[key][header]
                for key, header in kwargs.items()
                if header not in ["referer", "User-Agent"]
            }
            if len(headers) > 0:
                pargs[key] = headers
        elif key == "auth":
            if hasattr(kwargs[key], "token"):
                pargs[key] = f"Bearer {str(kwargs[key].token)}"  # type: ignore
            else:
                pargs[key] = f"{type(kwargs[key]).__name__}"  # type: ignore
        else:
            pargs[key] = kwargs[key]
    return f"Request: {method.upper()} {url}, payload: {pargs}"
