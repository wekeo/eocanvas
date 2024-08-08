import lxml.etree as etree

from .aggregator_avg import AggregatorAvg  # noqa: F401
from .aggregator_avg_outlier import AggregatorAvgOutlier  # noqa: F401
from .aggregator_minmax import AggregatorMinMax  # noqa: F401
from .aggregator_on_max_set import AggregatorOnMaxSet  # noqa: F401
from .aggregator_percentile import AggregatorPercentile  # noqa: F401
from .aggregator_sum import AggregatorSum  # noqa: F401


class Aggregators(object):
    def __init__(self, output_aggregators):
        self.output_aggregators = output_aggregators

    def to_xml(self):
        root = etree.Element("aggregators")

        for aggregator in self.output_aggregators:
            root.append(aggregator.to_xml())

        return root
