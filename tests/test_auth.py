import os
import time
from unittest.mock import mock_open, patch

import pytest

from eocanvas.auth import (
    CorruptedCredentialsError,
    Credentials,
    CredentialsNotFoundError,
    HTTPOAuth2,
    MalformedCredentialsError,
    OAuthToken,
)
from eocanvas.config import get_credentials_filepath


class MockHTTPRequest:
    def __init__(self):
        self.headers = {}


@pytest.fixture
def set_env(tmp_path):
    os.environ["EOCANVAS_CONFIG_DIR"] = str(tmp_path)
    yield
    del os.environ["EOCANVAS_CONFIG_DIR"]


def test_credentials_malformed():
    with pytest.raises(MalformedCredentialsError):
        Credentials("a a", "b/b")


def test_credentials_save_and_load(set_env):
    c = Credentials("abc", "123")
    c.save()
    assert get_credentials_filepath().exists()

    c = Credentials.load()
    assert c.username == "abc"
    assert c.password == "123"


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_credentials_corrupted(mock_open, mock_safe_load):
    mock_safe_load.return_value = "something"
    with pytest.raises(CorruptedCredentialsError):
        Credentials.load()

    mock_open.assert_called_once_with(get_credentials_filepath())


@patch("builtins.open", new_callable=mock_open)
def test_credentials_missing(mock_open):
    mock_open.side_effect = FileNotFoundError()
    with pytest.raises(CredentialsNotFoundError):
        Credentials.load()

    mock_open.assert_called_once_with(get_credentials_filepath())


def test_token_new_expired():
    token = OAuthToken("someurl", None)
    assert token.is_expired


@patch("eocanvas.auth.post")
def test_token(mock_post):
    mock_post.return_value.json.return_value = {
        "access_token": "abc",
        "refresh_token": "def",
        "expires_in": 1,
    }

    token = OAuthToken("someurl", Credentials("u", "p"))
    assert token.access_token == "abc"
    mock_post.assert_called_once()
    assert not token.is_expired
    time.sleep(2)
    assert token.is_expired


@patch("eocanvas.auth.OAuthToken")
def test_http_oauth(mock_token):
    mock_token.__str__.return_value = "abc"
    mock_prepared_request = MockHTTPRequest()
    HTTPOAuth2(mock_token)(mock_prepared_request)
    assert mock_prepared_request.headers["authorization"] == "Bearer abc"
