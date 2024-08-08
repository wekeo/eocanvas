"""Code in this package is largely based on https://github.com/snap-contrib/snapista/.

Snapista requires a local instance of Snap.
We unwired the dependency as we only need to build or load the graph.
All the operators are statically listed.
"""

from .graph import Graph  # noqa: F401
from .operator import Operator  # noqa: F401
from .operatorparams import OperatorParams  # noqa: F401
from .target_band import TargetBand  # noqa: F401
from .target_band_descriptors import TargetBandDescriptors  # noqa: F401
