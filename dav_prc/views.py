

from django.http import HttpResponse
from django.core.files.temp import NamedTemporaryFile
from django.views.decorators.gzip import gzip_page

from eoxserver.resources.coverages.models import Coverage
from eoxserver.backends.access import connect

from subprocess import CalledProcessError, check_output, Popen
from os.path import abspath, basename, getsize
from os import stat

# default 15 days
MAX_AGE = 1296000

@gzip_page
def coverage(request, identifier):
    cov = Coverage.objects.get(identifier=identifier)

    filename = connect(cov.data_items.filter(semantic__startswith="band")[0])

    size = getsize(filename)

    if size>(100*1024*1024):
        tmpfile = NamedTemporaryFile(suffix='.tif')

        cmd_args = ['gdal_translate', '-outsize', '7%', '7%', filename, tmpfile.name]
        process = check_output(cmd_args)

        #returnfile = FileWrapper(tmpfile)
        returnfile = tmpfile
        size = getsize(tmpfile.name)
        
    else:
        returnfile = open(filename)


    response = HttpResponse(returnfile)
    response['Content-Type'] = 'image/tif'
    response['Content-Length'] = size
    response['Content-Disposition'] = 'attachment; filename=%s' % basename(filename)
    response['Cache-Control'] = 'max-age=%d' % MAX_AGE

    return response