import json
from dataclasses import dataclass, field
from typing import List

from .api import Config, Input, Process
from .snap.graph import Graph


@dataclass
class SnapParams:
    snap_graph: Graph
    eo_input: List[Input] = field(default_factory=list)
    eo_config: List[Config] = field(default_factory=list)


@dataclass
class SnapProcess(Process, SnapParams):
    def __post_init__(self):
        if self.process_id is None:
            self.process_id = "snap-function"

        if not isinstance(self.eo_config, list):
            self.eo_config = [self.eo_config]

        if not isinstance(self.eo_input, list):
            self.eo_input = [self.eo_input]

    def prepare_inputs(self):
        return {
            "inputs": {
                "snap_graph": self.snap_graph.b64encode(),
                "eo_input": json.dumps([i.asdict() for i in self.eo_input]),
                "eo_config": json.dumps([c.asdict() for c in self.eo_config]),
            },
            "outputs": {},
            "response": "raw",
            "subscriber": None,
        }


@dataclass
class DataTailorParams:
    epct_chain: str  # TODO
    epct_input: List[Input] = field(default_factory=list)


@dataclass
class DataTailorProcess(Process, DataTailorParams):
    def __post_init__(self):
        if self.process_id is None:
            self.process_id = "dataTailor"

        if not isinstance(self.epct_input, list):
            self.epct_input = [self.epct_input]

    def prepare_inputs(self):
        return {
            "inputs": {
                "epct_chain": self.epct_chain,  # TODO
                "epct_input": json.dumps([i.asdict() for i in self.epct_input]),
            },
            "outputs": {},
            "response": "raw",
            "subscriber": None,
        }
