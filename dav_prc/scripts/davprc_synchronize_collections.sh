#!/bin/bash

BASEDIR="/das-dave_data/mwcs/"

for directory in "$BASEDIR/*/" ; do
    collection="$(basename $directory)"
    python /srv/dav-prc/manage.py eoxs_id_check $collection
    if [ $? -eq 0 ] ; then
        echo ">> Creating new collection '$collection'"
        davpprc_add_collection.sh "$BASEDIR/$collection"
    fi

    echo ">> Synchronizing collection '$collection'"

    python /srv/dav-prc/manage.py eoxs_collection_synchronize -i "$collection"
done
