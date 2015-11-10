INSTANCE_DIR=/srv/dav-prc/
WATCH_DIR=/das-dave_data/mwcs/

pushd $INSTANCE_DIR

inotifywait -m $WATCH_DIR -e create -e delete -e moved_to -e moved_from |

   while read path action file; do

       if [ $action = "CREATE,ISDIR" ] || [ $action = "MOVED_TO,ISDIR" ] ; then
           echo "Directory $file created."
           #python manage.py eoxs_collection_create -i $file
           #python manage.py eoxs_collection_datasource -i $file -s "$WATCH_DIR/$file/*tif" -t "%(root)s.xml"

           davprc_add_collection.sh $file

       elif [ $action = "DELETE,ISDIR" ] || [ $action = "MOVED_FROM,ISDIR" ] ; then
           echo "Directory $file deleted."
           python manage.py eoxs_collection_delete -i $file
           # TODO: delete range-type aswell
       fi
   done

popd
