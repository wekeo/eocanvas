import pytest
import requests

from eocanvas.exceptions import HTTPError
from eocanvas.http import delete, get, patch, post, put


class MockHTTPResponse:
    def __init__(self, status_code, text=None):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        """Just to mimic the original"""
        pass


def test_request_calls(monkeypatch):
    def mock_session_call(*args, **kwargs):
        return MockHTTPResponse(200)

    monkeypatch.setattr(requests.Session, "get", mock_session_call)
    monkeypatch.setattr(requests.Session, "post", mock_session_call)
    monkeypatch.setattr(requests.Session, "patch", mock_session_call)
    monkeypatch.setattr(requests.Session, "put", mock_session_call)
    monkeypatch.setattr(requests.Session, "delete", mock_session_call)

    assert get("https://test.test").status_code == 200
    assert post("https://test.test").status_code == 200
    assert patch("https://test.test").status_code == 200
    assert put("https://test.test").status_code == 200
    assert delete("https://test.test").status_code == 200


def test_get_with_retries():
    with pytest.raises(HTTPError):
        get("https://httpstat.us/500")
