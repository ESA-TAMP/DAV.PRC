#!/bin/bash

BASEDIR="/tamplocal/das-dave/mwcs"
SITE_BASEDIR="/tamplocal/das-dave/groundMeasurements"

# checking all existing folders in the base directory
for directory in `ls $BASEDIR` ; do
    collection=$(basename "$directory")
    echo ">> Inspecting collection '$collection'"

    # check if the collection already exists
    python /srv/dav-prc/manage.py eoxs_id_check $collection > /dev/null && {
         # if the collection does not yet exist, create a new collection
        echo ">> Creating new collection '$collection'"
        davprc_add_collection.sh "$BASEDIR/$collection"
    }

    # synchronize the collection to see if new datasets need to be created
    echo ">> Synchronizing collection '$collection'"
    python /srv/dav-prc/manage.py eoxs_collection_synchronize -i "$collection"
done

for directory in `ls $SITE_BASEDIR` ; do
    collection=$(basename "$directory")
    echo ">> Inspecting site collection '$collection'"

    # check if the collection already exists
    python /srv/dav-prc/manage.py eoxs_id_check $collection > /dev/null && {
        # if the collection does not yet exist, create a new collection
        echo ">> Creating new site collection '$collection'"
        davprc_add_site_collection.sh "$SITE_BASEDIR/$collection"
    }

    # synchronize the collection to see if new datasets need to be created
    echo ">> Synchronizing site collection '$collection'"
    python /srv/dav-prc/manage.py eoxs_collection_synchronize -i "$collection"
done


# check all registered collections
output=`python /srv/dav-prc/manage.py eoxs_id_list -s -t DatasetSeries`
if [[ $output == SpatiaLite* ]] ; then
    output=`echo "$output" | tail -n +12`
fi

for identifier in $output ; do
    # if the collection does not have a folder-counterpart, remove that 
    # collection and all its contents
    if [ ! -d "$BASEDIR/$identifier" ] && [ ! -d "$SITE_BASEDIR/$identifier" ] ; then
        echo ">> Collection '$identifier' was removed. Deleting remnants."
        python /srv/dav-prc/manage.py eoxs_collection_purge -d -i $identifier
    fi
done
