#!/bin/bash

COLLECTION=$(basename "$1")

numbands=$(cat "$1/DescribeCoverage" | cut -d" " -f11)

create_rangetype_definition() {
    name=$1
    count=$2

    echo "[{\"name\": \"${name}\", \"data_type\": \"UInt16\", \"bands\": ["
    for i in $(seq 1 $count) ; do
        echo "
            {
                \"definition\": \"http://www.opengis.net/def/property/OGC/0/Radiance\",
                \"description\": \"$name band $i\",
                \"gdal_interpretation\": \"Undefined\",
                \"identifier\": \"${name}_${i}\",
                \"name\": \"${name}_${i}\",
                \"uom\": \"undefined\",
                \"nil_values\": []
            }"
        if [ "$i" != "$count" ] ; then
            echo ","
        fi
    done
    echo "]}]"
}

echo `create_rangetype_definition $COLLECTION $numbands` | python /srv/dav-prc/manage.py eoxs_rangetype_load

python /srv/dav-prc/manage.py eoxs_collection_create -i $COLLECTION
python /srv/dav-prc/manage.py eoxs_collection_datasource -i $COLLECTION -s "$1/*/*/*/*/*/*/*.tif" -t "{source}.xml"

