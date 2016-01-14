from django.contrib.gis.db import models
from eoxserver.resources.coverages import models as coverages


class SiteDataset(coverages.Coverage):
    objects = models.GeoManager()

    location = models.PointField()
    elevation = models.FloatField()

coverages.EO_OBJECT_TYPE_REGISTRY[601] = SiteDataset
