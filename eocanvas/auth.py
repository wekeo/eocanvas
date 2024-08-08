from __future__ import annotations

import re
import time
from urllib.parse import urljoin

import requests
import yaml
from requests.auth import AuthBase

from .config import get_credentials_filepath
from .exceptions import (
    CorruptedCredentialsError,
    CredentialsNotFoundError,
    MalformedCredentialsError,
)
from .http import post
from .logging import logger


class Credentials:
    """Provides basic credentials functionalities, such as save on or load from file."""

    def __init__(self, username: str, password: str) -> None:
        umatch = re.match(r"[^\s]+$", username)
        pmatch = re.match(r"[^\s]+$", password)
        if umatch is None or pmatch is None:
            raise MalformedCredentialsError(
                "Username and/or password malformed. Please review them."
            )
        self.username = username
        self.password = password

    def save(self) -> None:
        credentials_path = get_credentials_filepath(True)
        try:
            credentials = {
                "user": self.username,
                "password": self.password,
            }
            with credentials_path.open(mode="w") as f:
                yaml.dump(credentials, f, default_flow_style=False)

            logger.info(f"Credentials are written to file {credentials_path}")
        except OSError:
            logger.error(
                "Credentials could not be written to {credentials_path}."
                "Please review your configuration."
            )

    @classmethod
    def load(cls) -> Credentials:
        credentials_path = get_credentials_filepath()
        try:
            with open(credentials_path) as f:
                credentials = yaml.safe_load(f)
                return cls(credentials["user"], credentials["password"])
        except (KeyError, TypeError):
            raise CorruptedCredentialsError(
                f"Credentials could not be read from {credentials_path}. Please save them again."
            )
        except FileNotFoundError:
            raise CredentialsNotFoundError(
                f"Missing credentials file at {credentials_path}. Please save them again."
            )


class OAuthToken:
    """OAuth token handler."""

    def __init__(self, url: str, credentials: Credentials, verify_ssl=True):
        self.url = url
        self.credentials = credentials
        self.verify_ssl = verify_ssl
        self._access_token = None
        self._refresh_token = None
        self._expiration_time = None

    def __str__(self) -> str:
        return self.access_token

    @property
    def is_expired(self) -> bool:
        now = int(time.time())
        return self._expiration_time is None or now > self._expiration_time

    @property
    def access_token(self) -> str:
        """The access token to the API.

        :return: A valid OAuth Access Token.
        :rtype: str
        """
        if self.is_expired:
            logger.debug("Token expired or invalid. Requesting a new one.")
            self._set_token()

        return self._access_token

    def invalidate(self) -> None:
        self._expiration_time = None

    def _set_token(self) -> None:
        """Requests and set a new access token using the configured credentials."""

        def get_token():
            return post(
                urljoin(self.url, "gettoken"),
                json={
                    "username": self.credentials.username,
                    "password": self.credentials.password,
                },
                verify=self.verify_ssl,
            )

        def refresh_token():
            return post(
                urljoin(self.url, "refreshtoken"),
                data={"refresh_token": self._refresh_token},
                verify=self.verify_ssl,
            )

        if self._refresh_token is not None:
            response = refresh_token()
            if response.status_code in (
                requests.codes.forbidden,
                requests.codes.bad_request,
            ):
                response = get_token()
        else:
            response = get_token()

        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._expiration_time = int(time.time()) + data["expires_in"]


class HTTPOAuth2(AuthBase):
    """HTTP authentication to be used with requests. Set an bearer authorization header."""

    def __init__(self, token: OAuthToken):
        self.token = token

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        request.headers["authorization"] = f"Bearer {self.token}"
        return request
