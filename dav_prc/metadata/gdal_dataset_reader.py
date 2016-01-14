
from datetime import datetime, date, time
from os.path import splitext, split, basename

from django.utils.timezone import utc, make_aware
from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core import Component, implements
from eoxserver.resources.coverages.metadata.interfaces import (
    GDALDatasetMetadataReaderInterface
)


class DAVPRCGDALMetadataFormatReader(Component):
    """ Metadata format reader for specific ENVISAT products.
    """
    implements(GDALDatasetMetadataReaderInterface)

    def test_ds(self, ds):
        """ Check whether or not the dataset seems to be an ENVISAT image and
            has the correct metadata tags.
        """
        return True

    def read_ds(self, ds):
        """ Return the ENVISAT specific metadata items.
        """

        filename = ds.GetFileList()[0]

        path, data_file = split(filename)

        #assert(len(parts) >= 8)
        parts = path.split("/")[-7:]

        raw_time = parts[4]

        timestamp = datetime.combine(
            date(*map(int, parts[1:4])),
            time(int(raw_time[:2]), int(raw_time[2:4]), int(raw_time[4:]))
        )
        timestamp = make_aware(timestamp, utc)

        size = (ds.RasterXSize, ds.RasterYSize)
        gt = ds.GetGeoTransform()

        def gtrans(x, y):
            return gt[0] + x*gt[1] + y*gt[2], gt[3] + x*gt[4] + y*gt[5]
        vpix = [(0, 0), (0, size[1]), (size[0], 0), (size[0], size[1])]
        vx, vy = zip(*(gtrans(x, y) for x, y in vpix))

        return {
            "identifier": splitext(basename(filename))[0],
            "begin_time": timestamp,
            "end_time": timestamp,
            "range_type_name": parts[0],
            "footprint": MultiPolygon(Polygon.from_bbox(
                (min(vx), min(vy), max(vx), max(vy))
            )),
            # "begin_time": parse_datetime(ds.GetMetadataItem("MPH_SENSING_START")),
            # "end_time": parse_datetime(ds.GetMetadataItem("MPH_SENSING_STOP"))
        }
