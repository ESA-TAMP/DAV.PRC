#!/bin/bash

BASEDIR="/das-dave_data/mwcs/"
alias MANAGE="python /srv/dav-prc/manage.py"

for directory in "$BASEDIR/*/" ; do
    collection="$(basename $directory)"
    if [ MANAGE eox_id_check $collection -eq 0 ] ; then
        davpprc_add_collection.sh "$BASEDIR/$collection"
    fi

    MANAGE eoxs_collection_synchronize -i "$collection"
done
