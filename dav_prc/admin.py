from eoxserver.resources.coverages import admin

from dav_prc import models


class SiteDatasetAdmin(admin.CoverageAdmin):
    model = models.SiteDataset

    inlines = (admin.DataItemInline, admin.CollectionInline)

    fieldsets = (
        (None, {
            'fields': ('identifier', )
        }),
        ('Metadata', {
            'fields': ('range_type',
                       ('size_x', 'size_y'),
                       ('min_x', 'min_y'),
                       ('max_x', 'max_y'),
                       ('srid', 'projection'),
                       ('begin_time', 'end_time'),
                       'footprint',
                       'visible',
                       'location',
                       'elevation'),
            'description': 'Geospatial metadata'
        }),
    )

admin.admin.site.register(models.SiteDataset, SiteDatasetAdmin)
