"""Data Tailor classes.

Most of the code has been taken from the official EUMDAC library.
Changes have been made to the Chain class to create instances from a yaml file and
to encode it to base64 representation as required by the API.
"""
import sys
from base64 import b64encode
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Optional, Union

import yaml

if sys.version_info < (3, 9):
    from typing import MutableMapping
else:
    from collections.abc import MutableMapping


def _none_filter(*args: Any, **kwargs: Any) -> MutableMapping[str, Any]:
    """Build a mapping of '*args' and '**kwargs' removing None values."""
    return {k: v for k, v in dict(*args, **kwargs).items() if v is not None}


class AsDictMixin:
    """Base class adding an 'asdict' method that removes None values."""

    def asdict(self) -> MutableMapping[str, Any]:
        """Return the fields of the instance as a new dictionary mapping field names to
        field values, removing None values."""
        return asdict(self, dict_factory=_none_filter)  # type: ignore


@dataclass
class Filter(AsDictMixin):
    """Layer filter, a list of `bands` or layers for a given `product`.

    Attributes
    ----------
    - `id`: *str*
    - `name`: *str*
        Human readable name.
    - `product`: *str*
        Product that the filter applies to.
    - `bands`: *list[dict]*
        List of bands part of the filter, as dicts of {id, number, name}.
    """

    id: Optional[str] = None
    bands: Optional[list] = None  # type: ignore[type-arg]
    name: Optional[str] = None
    product: Optional[str] = None


@dataclass
class RegionOfInterest(AsDictMixin):
    """Region of interest, a geographical area defined by its `NSWE` coordinates.

    Attributes
    ----------
    - `id`: *str*
    - `name`: *str*
        Human readable name.
    - `description`: *str*
        Human readable description.
    - `NSWE`:
        North, south, west, east coordinates, in decimal degrees.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    NSWE: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Quicklook(AsDictMixin):
    """Configuration for generating quicklooks."""

    id: Optional[str] = None
    name: Optional[str] = None
    resample_method: Optional[str] = None
    stretch_method: Optional[str] = None
    product: Optional[str] = None
    format: Optional[str] = None
    nodatacolor: Optional[str] = None
    filter: Union[None, dict, Filter] = None  # type: ignore[type-arg]
    x_size: Optional[int] = None

    def __post_init__(self) -> None:
        """Prepare `filter` as a Filter instance if given as dict."""
        if self.filter is not None and isinstance(self.filter, dict):
            self.filter = Filter(**self.filter)


@dataclass
class Chain(AsDictMixin):
    """Chain configuration for Data Tailor customisation jobs."""

    __submodels = {"filter": Filter, "roi": RegionOfInterest, "quicklook": Quicklook}
    id: Optional[str] = None
    product: Optional[str] = None
    format: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    aggregation: Optional[str] = None
    projection: Optional[str] = None
    roi: Union[None, dict, RegionOfInterest] = None  # type: ignore[type-arg]
    filter: Union[None, dict, Filter] = None  # type: ignore[type-arg]
    quicklook: Union[None, dict, Quicklook] = None  # type: ignore[type-arg]
    resample_method: Optional[str] = None
    resample_resolution: Optional[list] = None  # type: ignore[type-arg]
    compression: Optional[dict] = None  # type: ignore[type-arg]
    xrit_segments: Optional[list] = None  # type: ignore[type-arg]

    def __post_init__(self) -> None:
        """Prepare attributes as an instance of their class if given as dict."""
        for name, model in self.__submodels.items():
            attr = getattr(self, name)
            if attr is not None and isinstance(attr, Mapping):
                setattr(self, name, model(**attr))

    @classmethod
    def from_file(cls, filepath: str) -> "Chain":
        with open(filepath) as f:
            return cls(**yaml.safe_load(f))

    def b64encode(self) -> str:
        return b64encode(yaml.dump(self.asdict()).encode()).decode()
