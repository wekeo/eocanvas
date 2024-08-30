import os
from base64 import b64decode

import pytest
import yaml

from eocanvas.datatailor import Chain
from eocanvas.exceptions import InvalidChainError


def test_chain_load():
    filename = f"{os.path.dirname(__file__)}/data/chain.yaml"
    c = Chain.from_file(filename)
    encoded = c.b64encode()
    c2 = yaml.safe_load(b64decode(encoded))
    assert c.asdict() == c2


def test_chain_load_invalid():
    filename = f"{os.path.dirname(__file__)}/data/chain.yaml"
    with pytest.raises(InvalidChainError):
        Chain.from_file(filename)
