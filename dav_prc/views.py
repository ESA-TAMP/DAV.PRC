

from django.http import HttpResponse
from eoxserver.resources.coverages.models import Coverage
from eoxserver.backends.access import connect

from os.path import abspath, basename
from os import stat

# default 15 days
MAX_AGE = 1296000

def coverage(request, identifier):
    cov = Coverage.objects.get(identifier=identifier)

    filename = connect(cov.data_items.filter(semantic__startswith="band")[0])

    response = HttpResponse(open(filename))
    response['Content-Type'] = 'image/tif'
    response['Content-Length'] = stat(filename).st_size
    response['Content-Disposition'] = 'attachment; filename=%s' % basename(filename)
    response['Cache-Control'] = 'max-age=%d' % MAX_AGE

    return response