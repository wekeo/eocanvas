import json
from dataclasses import dataclass, field
from datetime import datetime
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
        }
        if self.eo_config:
            config_list = [c.asdict() for c in self.eo_config]
            inputs["inputs"]["eo_config"] = json.dumps(config_list)

        return inputs


@dataclass
class _DataTailorParams:
    epct_chain: Chain
    epct_input: List[Input] = field(default_factory=list)
    epct_config: List[Config] = field(default_factory=list)


@dataclass
class DataTailorProcess(Process, _DataTailorParams):
    def __post_init__(self):
        super().__post_init__()
        if self.process_id is None:
            self.process_id = "dataTailor"

        if not isinstance(self.epct_config, list):
            self.epct_config = [self.epct_config]

        if not isinstance(self.epct_input, list):
            self.epct_input = [self.epct_input]

    def prepare_inputs(self) -> Dict:
        inputs = super().prepare_inputs()
        inputs["inputs"] = {
            "epct_chain": self.epct_chain.b64encode(),
            "epct_input": json.dumps([i.asdict() for i in self.epct_input]),
        }
        if self.epct_config:
            config_list = [c.asdict() for c in self.epct_config]
            inputs["inputs"]["epct_config"] = json.dumps(config_list)

        return inputs


@dataclass
class ShearWaterParams:
    area: str
    start_day: str
    end_day: str

    valid_areas: set = field(default_factory=lambda: {"Sindian"}, init=False, repr=False)


@dataclass
class ShearWaterProcess(Process, ShearWaterParams):
    def __post_init__(self):
        super().__post_init__()
        if self.process_id is None:
            self.process_id = "shearwater-demo"

        if self.area not in self.valid_areas:
            raise ValueError(f"Invalid area '{self.area}'. Must be one of {self.valid_areas}.")

        for date_field_name in ["start_day", "end_day"]:
            date_value = getattr(self, date_field_name)
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"{date_field_name} '{date_value}' is not in YYYY-MM-DD format.")

    def prepare_inputs(self) -> Dict:
        inputs = super().prepare_inputs()
        inputs["inputs"] = {
            "area": self.area,
            "startDay": self.start_day,
            "endDay": self.end_day,
        }
