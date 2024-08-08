from pathlib import Path

import pytest

from eocanvas.config import URLs

CURRENT_DIR = Path(__file__).parent


def test_valid_urls():
    urls = URLs(urlfile=CURRENT_DIR / "data" / "valid_urls.yaml")
    assert urls.base_url == "someotherurl"
    assert urls.get("process_list") == "someotherurl/processes"
    assert urls.get("process_detail", process_id="5") == "someotherurl/processes/5"


def test_invalid_urls():
    with pytest.raises(KeyError):
        URLs(urlfile=CURRENT_DIR / "data" / "invalid_urls.yaml")
