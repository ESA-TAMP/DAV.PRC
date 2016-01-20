#!/bin/sh -e

# allow a custom location to override the default one if needed
export ROOT=${1:-"/var/dav-prc"}
export INSTANCE="/srv/dav-prc"

# Locate sudo (when available) for commands requiring the superuser.
# Allows setup of a custom autoconf instance located in the non-root user-space.
SUDO=`which sudo`

# Add CRS 900913 if not present
if ! grep -Fxq "<900913> +proj=tmerc +lat_0=0 +lon_0=21 +k=1 +x_0=21500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs  <>" /usr/share/proj/epsg ; then
    $SUDO sh -c 'echo "# WGS 84 / Pseudo-Mercator" >> /usr/share/proj/epsg'
    $SUDO sh -c 'echo "<900913> +proj=tmerc +lat_0=0 +lon_0=21 +k=1 +x_0=21500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs  <>" >> /usr/share/proj/epsg'
fi

# 
cd "$ROOT/"
$SUDO python setup.py develop

cd "$ROOT/eoxserver"
$SUDO python setup.py develop --no-deps

cd $INSTANCE

# # Prepare DBs
python manage.py syncdb --noinput --traceback

# Create admin user
python manage.py shell 1>/dev/null 2>&1 <<EOF
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
if authenticate(username='admin', password='admin') is None:
    User.objects.create_user('admin','office@eox.at','admin')
EOF

# Collect static files
python manage.py collectstatic --noinput
