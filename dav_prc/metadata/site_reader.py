from django.contrib.gis.geos import Point, MultiPolygon

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.util.xmltools import parse
from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface
)


class SiteFormatReader(Component):
    implements(MetadataReaderInterface)

    def test(self, obj):
        tree = parse(obj)
        print obj, tree
        return tree is not None and tree.getroot().tag == "site"

    def read(self, obj):
        tree = parse(obj)
        if self.test(tree):
            decoder = SiteFormatDecoder(tree)
            location = Point(decoder.longitude, decoder.latitude)

            print decoder.start_times, decoder.end_times
            return {
                "identifier": decoder.identifier,
                "location": location,
                "footprint": MultiPolygon(location.buffer(0.01)),
                "elevation": decoder.elevation,
                "coverage_type": "",
                "size": (decoder.size, 1),
                "projection": 4326,
                "begin_time": min(decoder.start_times),
                "end_time": max(decoder.end_times),
                "extent": (0, 0, 1, 1),
                "coverage_type": "dav_prc.models.SiteDataset"
            }
        raise Exception("Could not parse from obj '%r'." % obj)


class SiteFormatDecoder(xml.Decoder):
    identifier = xml.Parameter("siteName/text()", type=str, num=1)
    latitude = xml.Parameter("siteLatitude/text()", type=float, num=1)
    longitude = xml.Parameter("siteLongitude/text()", type=float, num=1)
    elevation = xml.Parameter("siteElevation/text()", type=float, num=1)
    size = xml.Parameter("count(data/entry)", type=int, num=1)
    start_times = xml.Parameter("data/entry/timeStart/text()", type=parse_iso8601, num="+")
    end_times = xml.Parameter("data/entry/timeEnd/text()", type=parse_iso8601, num="+")
