import os
import xml.etree.ElementTree as ET
from base64 import b64decode

from eocanvas.snap.graph import Graph


def test_graph_load():
    filename = f"{os.path.dirname(__file__)}/data/graph.xml"
    g = Graph.from_uri(filename)
    encoded = g.b64encode()
    g2 = Graph.from_text(b64decode(encoded))
    assert ET.tostring(g.root) == ET.tostring(g2.root)
