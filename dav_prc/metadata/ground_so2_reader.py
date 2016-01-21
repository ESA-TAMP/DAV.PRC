from django.contrib.gis.geos import Point, MultiPolygon

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.util.xmltools import parse
from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface
)


class GroundSO2FormatReader(Component):
    implements(MetadataReaderInterface)

    def test(self, obj):
        tree = parse(obj)
        return tree is not None and tree.getroot().tag == "groundSO2"

    def read(self, obj):
        tree = parse(obj)
        if self.test(tree):
            decoder = GroundSO2FormatDecoder(tree)
            location = Point(decoder.longitude, decoder.latitude)

            return {
                "identifier": decoder.identifier,
                "location": location,
                "footprint": MultiPolygon(location.buffer(0.01)),
                "elevation": decoder.elevation,
                "coverage_type": "",
                "size": (decoder.size, 1),
                "projection": 4326,
                "begin_time": min(decoder.times),
                "end_time": max(decoder.times),
                "extent": (0, 0, 1, 1),
                "coverage_type": "dav_prc.models.SiteDataset"
            }
        raise Exception("Could not parse from obj '%r'." % obj)


class GroundSO2FormatDecoder(xml.Decoder):
    identifier = xml.Parameter("@station", type=str, num=1)
    latitude = xml.Parameter("@latitude", type=float, num=1)
    longitude = xml.Parameter("@longitude", type=float, num=1)
    elevation = xml.Parameter("@height", type=float, num=1)
    size = xml.Parameter("count(dailyAverage)", type=int, num=1)
    times = xml.Parameter("dailyAverage/@date", type=parse_iso8601, num="+")
