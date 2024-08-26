import os
from base64 import b64decode

import yaml

from eocanvas.datatailor import Chain


def test_chain_load():
    filename = f"{os.path.dirname(__file__)}/data/chain.yaml"
    c = Chain.from_file(filename)
    encoded = c.b64encode()
    c2 = yaml.safe_load(b64decode(encoded))
    assert c.asdict() == c2
