#!/bin/bash

COLLECTION=$(basename "$1")
desc=`ls $1/*json`

python -c "
import json 
data = json.load(open('$desc'))['Collections'][0]
band = data['bands'][0]
band['nil_values'] = []
band.setdefault('description', '')
print json.dumps(data)
" | python /srv/dav-prc/manage.py eoxs_rangetype_load --traceback

python /srv/dav-prc/manage.py eoxs_collection_create -i $COLLECTION
python /srv/dav-prc/manage.py eoxs_collection_datasource -i $COLLECTION -s "$1/*.xml"

