import os
from base64 import b64encode
from urllib.parse import urlparse
from xml.sax.saxutils import unescape

import lxml.etree as etree
import requests
import yaml

from .binning import Aggregators, BinningVariables
from .binning.output_bands import BinningOutputBands
from .target_band_descriptors import TargetBandDescriptors


class Graph:
    """SNAP Graph class

    This class provides the methods to create, view and run a SNAP Graph

    Attributes:
        None.
    """

    def __init__(self, wdir=".", root=None):
        if root is None:
            self.root = etree.Element("graph")
            version = etree.SubElement(self.root, "version")
            version.text = "1.0"
        else:
            self.root = root

        self.pid = None
        self.p = None
        self.wdir = wdir

    def __str__(self):
        return "working dir: {}\n\n{}".format(
            self.wdir,
            etree.tostring(self.root, pretty_print=True).decode("utf-8"),
        ).replace("\\n", "\n")

    def __repr__(self):
        return "Graph(wdir='{}')".format(self.wdir)

    @classmethod
    def from_text(cls, text):
        root = etree.fromstring(text)
        return cls(root=root)

    @classmethod
    def from_uri(cls, uri):
        parsed = urlparse(uri)
        if parsed.scheme.startswith("http"):
            r = requests.get(uri)
            root = etree.fromstring(r.content).xpath("/graph")[0]
        else:
            root = etree.parse(uri).getroot()

        return cls(root=root)

    @staticmethod
    def list_operators():
        """This function provides a Python dictionary with all SNAP operators.

        Args:
            None.

        Returns
            Python dictionary with all SNAP operators.

        Raises:
            None.
        """
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/operators.yaml")
        with open(filename) as f:
            operators = yaml.safe_load(f)

        return list(operators.keys())

    @staticmethod
    def describe_operators():
        """This function provides a Python dictionary with all SNAP operators.

        Args:
            None.

        Returns
            Python dictionary with all SNAP operators.

        Raises:
            None.
        """
        with open("data/operators.yaml") as f:
            operators = yaml.safe_load(f)

        descriptions = {key: value["desc"] for key, value in operators.items()}

        for op, desc in descriptions.items():
            print(f"{op} - {desc}")

        return descriptions

    def b64encode(self):
        graph = etree.tostring(self.root, pretty_print=True)
        return b64encode(graph).decode()

    def nice_view(self):
        try:
            import IPython
            from IPython.display import HTML
            from pygments import highlight
            from pygments.formatters import HtmlFormatter
            from pygments.lexers import XmlLexer

            def display_xml_nice(xml):
                formatter = HtmlFormatter()
                IPython.display.display(
                    HTML(
                        '<style type="text/css">{}</style>    {}'.format(
                            formatter.get_style_defs(".highlight"),
                            highlight(xml, XmlLexer(), formatter),
                        )
                    )
                )

            display_xml_nice(etree.tostring(self.root, pretty_print=True))

        except ModuleNotFoundError:
            print(
                etree.tostring(self.root, pretty_print=True).decode("utf-8").replace("\\n", "\n")
            )

    def view(self):
        """This method prints SNAP Graph

        Args:
            None.

        Returns
            None.

        Raises:
            None.
        """
        print(unescape(etree.tostring(self.root, pretty_print=True).decode("utf-8")))

    def add_node(self, operator, node_id, source=None):
        """This method adds or overwrites a node to the SNAP Graph

        Args:
            operator: SNAP operator
            node_id: node identifier
            source: string or list of sources (previous node identifiers in the SNAP Graph)

        Returns
            None.

        Raises:
            None.
        """
        xpath_expr = '/graph/node[@id="%s"]' % node_id

        if len(self.root.xpath(xpath_expr)) != 0:
            node_elem = self.root.xpath(xpath_expr)[0]
            operator_elem = self.root.xpath(xpath_expr + "/operator")[0]
            sources_elem = self.root.xpath(xpath_expr + "/sources")[0]
            parameters_elem = self.root.xpath(xpath_expr + "/parameters")

            for param in [
                name
                for name in dir(operator)
                if not name.startswith("__")
                and not name.endswith("__")
                and name != "_params"
                and name != "operator"
                and type(getattr(operator, name)).__name__
                in [
                    "str",
                    "NoneType",
                    "TargetBandDescriptors",
                    "Aggregators",
                    "BinningOutputBands",
                    "BinningVariables",
                ]
            ]:
                if param in [
                    "targetBandDescriptors",
                    "aggregatorConfigs",
                    "variableConfigs",
                    "bandConfigurations",
                    "postProcessorConfig",
                    "productCustomizerConfig",
                ]:
                    if param in [
                        "bandConfigurations",
                        "variableConfigs",
                        "postProcessorConfig",
                        "productCustomizerConfig",
                    ] and not getattr(operator, param):
                        continue

                    if (
                        isinstance(getattr(operator, param), TargetBandDescriptors)
                        or isinstance(getattr(operator, param), Aggregators)
                        or isinstance(getattr(operator, param), BinningOutputBands)
                        or isinstance(getattr(operator, param), BinningVariables)
                    ):
                        parameters_elem.append(getattr(operator, param).to_xml())

                    elif isinstance(getattr(operator, param), str):
                        parameters_elem.append(etree.fromstring(getattr(operator, param)))
                    else:
                        raise ValueError()

                else:
                    try:
                        p_elem = self.root.xpath(xpath_expr + "/parameters/%s" % param)[0]

                        if getattr(operator, param) is not None:
                            if getattr(operator, param)[0] != "<":
                                p_elem.text = getattr(operator, param)
                            else:
                                p_elem.text.append(etree.fromstring(getattr(operator, param)))
                    except IndexError:
                        pass

        else:
            node_elem = etree.SubElement(self.root, "node")
            operator_elem = etree.SubElement(node_elem, "operator")
            sources_elem = etree.SubElement(node_elem, "sources")

            if isinstance(source, list):
                for index, s in enumerate(source):
                    if index == 0:
                        source_product_elem = etree.SubElement(sources_elem, "sourceProduct")

                    else:
                        source_product_elem = etree.SubElement(
                            sources_elem, "sourceProduct.%s" % str(index)
                        )

                    source_product_elem.attrib["refid"] = s

            elif isinstance(source, dict):
                for key, value in source.iteritems():
                    source_product_elem = etree.SubElement(sources_elem, key)
                    source_product_elem.text = value

            elif source is not None:
                source_product_elem = etree.SubElement(sources_elem, "sourceProduct")
                source_product_elem.attrib["refid"] = source

            parameters_elem = etree.SubElement(node_elem, "parameters")
            parameters_elem.attrib["class"] = "com.bc.ceres.binding.dom.XppDomElement"

            for param in [
                name
                for name in dir(operator)
                if not name.startswith("__")
                and not name.endswith("__")
                and name != "_params"
                and name != "operator"
                and type(getattr(operator, name)).__name__
                in [
                    "str",
                    "NoneType",
                    "TargetBandDescriptors",
                    "Aggregators",
                    "BinningOutputBands",
                    "BinningVariables",
                ]
            ]:
                if param in [
                    "targetBandDescriptors",
                    "aggregatorConfigs",
                    "variableConfigs",
                    "bandConfigurations",
                    "postProcessorConfig",
                    "productCustomizerConfig",
                ]:
                    print(param, getattr(operator, param))
                    if param in [
                        "bandConfigurations",
                        "variableConfigs",
                        "postProcessorConfig",
                        "productCustomizerConfig",
                    ] and not getattr(operator, param):
                        continue

                    if (
                        isinstance(getattr(operator, param), TargetBandDescriptors)
                        or isinstance(getattr(operator, param), Aggregators)
                        or isinstance(getattr(operator, param), BinningOutputBands)
                        or isinstance(getattr(operator, param), BinningVariables)
                    ):
                        parameters_elem.append(getattr(operator, param).to_xml())

                    elif isinstance(getattr(operator, param), str):
                        parameters_elem.append(etree.fromstring(getattr(operator, param)))
                    else:
                        raise ValueError()

                else:
                    parameter_elem = etree.SubElement(parameters_elem, param)

                    if getattr(operator, param) is not None:
                        if getattr(operator, param)[0] != "<":
                            parameter_elem.text = getattr(operator, param)
                        else:
                            parameter_elem.append(etree.fromstring(getattr(operator, param)))

        node_elem.attrib["id"] = node_id

        operator_elem.text = operator.operator

    def save_graph(self, filename):
        """This method saves the SNAP Graph

        Args:
            filename: XML filename with '.xml' extension

        Returns
            None.

        Raises:
            None.
        """

        with open(filename, "w") as file:
            file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file.write(unescape(etree.tostring(self.root, pretty_print=True).decode()))
