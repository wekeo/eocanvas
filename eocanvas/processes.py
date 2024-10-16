import json
from dataclasses import dataclass, field
from typing import Dict, List

from .api import Config, Input, Process
from .datatailor.chain import Chain
from .snap.graph import Graph


@dataclass
class _SnapParams:
    snap_graph: Graph
    eo_input: List[Input] = field(default_factory=list)
    eo_config: List[Config] = field(default_factory=list)


@dataclass
class SnapProcess(Process, _SnapParams):
    def __post_init__(self):
        super().__post_init__()
        if self.process_id is None:
            self.process_id = "snap-function"

        if not isinstance(self.eo_config, list):
            self.eo_config = [self.eo_config]

        if not isinstance(self.eo_input, list):
            self.eo_input = [self.eo_input]

    def prepare_inputs(self) -> Dict:
        inputs = super().prepare_inputs()
        inputs["inputs"] = {
            "snap_graph": self.snap_graph.b64encode(),
            "eo_input": json.dumps([i.asdict() for i in self.eo_input]),
            "eo_config": json.dumps([c.asdict() for c in self.eo_config]),
        }

        return inputs


@dataclass
class _DataTailorParams:
    epct_chain: Chain
    epct_input: List[Input] = field(default_factory=list)


@dataclass
class DataTailorProcess(Process, _DataTailorParams):
    def __post_init__(self):
        super().__post_init__()
        if self.process_id is None:
            self.process_id = "dataTailor"

        if not isinstance(self.epct_input, list):
            self.epct_input = [self.epct_input]

    def prepare_inputs(self) -> Dict:
        inputs = super().prepare_inputs()
        inputs["inputs"] = {
            "epct_chain": self.epct_chain.b64encode(),
            "epct_input": json.dumps([i.asdict() for i in self.epct_input]),
        }

        return inputs
