import os
import sys
from importlib import resources
from pathlib import Path
from typing import Optional

import yaml


def get_credentials_dir(create: bool = False) -> Path:
    path = Path(os.getenv("EOCANVAS_CONFIG_DIR", Path.home()))
    if create:
        path.mkdir(exist_ok=True)
    return path


def get_credentials_filepath(create: bool = False) -> Path:
    return get_credentials_dir(create) / ".hdarc"


class URLs:
    def __init__(self, urlfile: Optional[str] = None):
        if urlfile is None:
            if sys.version_info >= (3, 9):
                with resources.as_file(resources.files("eocanvas").joinpath("urls.yaml")) as path:
                    with open(path) as f:
                        data = yaml.safe_load(f)
            else:  # python < 3.9
                with resources.path("eocanvas", "urls.yaml") as path:
                    with open(path) as f:
                        data = yaml.safe_load(f)

        else:
            with open(urlfile) as f:
                data = yaml.safe_load(f)

        try:
            self.token_url = data["token_url"]
            self.base_url = data["base_url"]
            self.endpoints = data["endpoints"]
        except KeyError as err:
            raise KeyError(f"Malformed url file: {err}")

    def get(self, endpoint_name: str, **kwargs) -> str:
        endpoint = self.endpoints.get(endpoint_name)
        if endpoint is None:
            raise ValueError(f"Endpoint {endpoint_name} not found in configuration.")
        return self.base_url + endpoint.format(**kwargs)
