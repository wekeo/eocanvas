# pytype: skip-file

"""
This module contains a utility to extract and save to a local json file all the
SNAP operators metadata.
It requires a full Snapista installation through conda or mamba and a local SNAP
instance, which comes with Snapista.
"""

import json
from typing import Dict

from snapista import Graph
from snappy import GPF, jpy

from .snap_types import OperatorType, ParamType


def get_formats(method):
    manager = jpy.get_type("org.esa.snap.core.dataio.ProductIOPlugInManager")
    if method == "Read":
        plugins = manager.getInstance().getAllReaderPlugIns()
    elif method == "Write":
        plugins = manager.getInstance().getAllWriterPlugIns()
    else:
        raise ValueError
    formats = []
    while plugins.hasNext():
        plugin = plugins.next()
        formats.append(plugin.getFormatNames()[0])
    return formats


def get_snap_operators() -> Dict[str, OperatorType]:
    operators = Graph.list_operators()
    d = {o: {} for o in operators}
    for o in operators:
        spi = GPF.getDefaultInstance().getOperatorSpiRegistry().getOperatorSpi(o)
        d[o]["alias"] = spi.getOperatorDescriptor().getAlias()
        d[o]["description"] = spi.getOperatorDescriptor().getDescription()
        d[o]["authors"] = spi.getOperatorDescriptor().getAuthors()
        d[o]["name"] = spi.getOperatorDescriptor().getName()
        d[o]["version"] = spi.getOperatorDescriptor().getVersion()
        d[o]["params"] = {}
        params = spi.getOperatorDescriptor().getParameterDescriptors()
        for param in params:
            d[o]["params"][param.getName()] = {}
            d[o]["params"][param.getName()]["name"] = param.getName()
            d[o]["params"][param.getName()]["description"] = param.getDescription()
            d[o]["params"][param.getName()]["default_values"] = param.getDefaultValue()
            if o == "Write" and param.getName() == "formatName":
                d[o]["params"][param.getName()]["values_set"] = get_formats("Write")
            elif o == "Read" and param.getName() == "formatName":
                d[o]["params"][param.getName()]["values_set"] = get_formats("Read")
            else:
                d[o]["params"][param.getName()]["values_set"] = list(param.getValueSet())
    return d


def serialize(operators: Dict[str, OperatorType], filename: str):
    with open(filename, "w") as f:
        json.dump(operators, f)


def deserialize(filename: str) -> Dict[str, OperatorType]:
    with open(filename) as f:
        operators = json.load(f)

    operators = {k: OperatorType(**v) for k, v in operators.items()}
    for k, v in operators.items():
        v["params"] = [ParamType(**p) for p in v["params"]]

    return operators
