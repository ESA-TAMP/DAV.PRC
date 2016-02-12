from uuid import uuid4
import csv
from itertools import izip
from lxml import etree

from django.utils.datastructures import SortedDict as OrderedDict
from eoxserver.core import Component, implements
from eoxserver.backends.access import connect
from eoxserver.services.ows.version import Version
from eoxserver.services.ows.wcs.interfaces import WCSCoverageRendererInterface
from eoxserver.services.exceptions import (
    InvalidSubsettingException, RenderException
)
from eoxserver.services.result import ResultFile
from eoxserver.services.subset import Trim

from dav_prc import models


class SiteRenderer(Component):
    """ A coverage renderer for VirES Products and Product Collections.
    """

    implements(WCSCoverageRendererInterface)

    versions = (Version(2, 0),)
    handles = (models.SiteDataset,)

    def supports(self, params):
        return issubclass(params.coverage.real_type, self.handles)

    def render(self, params):
        coverage = params.coverage.cast()
        frmt = params.format

        # get subset
        subset = self._apply_subsets(coverage, params.subsets)

        output_data = self._read_data(coverage, subset, params.rangesubset)

        result = self._encode_data(coverage, output_data, frmt)

        # TODO: coverage description if "multipart"
        return [result]

    def _apply_subsets(self, coverage, subsets):
        if len(subsets) > 1:
            raise InvalidSubsettingException(
                "Too many subsets supplied"
            )

        elif len(subsets):
            subset = subsets[0]

            if not isinstance(subset, Trim):
                raise InvalidSubsettingException(
                    "Invalid subsetting method: only trims are allowed"
                )

            if subset.is_temporal:
                begin_time, end_time = coverage.time_extent
                if subset.low < begin_time or subset.high > end_time:
                    raise InvalidSubsettingException(
                        "Temporal subset does not match coverage temporal "
                        "extent."
                    )

                resolution = get_total_seconds(coverage.resolution_time)
                low = get_total_seconds(subset.low - begin_time) / resolution
                high = get_total_seconds(subset.high - begin_time) / resolution

                subset = Trim("x", low, high)

            else:
                if subset.low < 0 or subset.high > coverage.size_x:
                    raise InvalidSubsettingException(
                        "Subset size does not match coverage size."
                    )

        else:
            subset = Trim("x", 0, coverage.size_x)

        return subset

    def _read_data(self, coverage, subset, rangesubset):
        range_type = coverage.range_type

        # Open file
        filename = connect(coverage.data_items.all()[0])

        root = etree.parse(filename).getroot()
        output_data = OrderedDict()

        # Read data

        band = range_type[0]
        if not rangesubset or band in rangesubset:
            data = map(float, root.xpath("data/entry/value/text()"))
            print data, root
            data = data[int(subset.low):int(subset.high)]
            output_data[band.identifier] = data

        return output_data

    def _encode_data(self, coverage, output_data, frmt):
        # Encode data
        if frmt == "text/csv":
            output_filename = "/tmp/%s.csv" % uuid4().hex
            with open(output_filename, "w+") as f:
                writer = csv.writer(f)
                writer.writerow(output_data.keys())
                for row in izip(*output_data.values()):
                    writer.writerow(row)

            return ResultFile(
                output_filename, "text/csv", "%s.csv" % coverage.identifier,
                coverage.identifier
            )

        else:
            raise RenderException("Invalid format '%s'" % frmt, "format")


def get_total_seconds(d):
    """ Helper to calculate the total seconds of a timedelta
    """
    try:
        return d.total_seconds()
    except:
        return (d.microseconds + (d.seconds + d.days * 24 * 3600) * 1e6) / 1e6
