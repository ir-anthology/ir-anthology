#!/usr/bin/env sh
rebuild=$1
echo $rebuild
set -e
if [ $rebuild = true ] ; then
    qlever get-data
    qlever index --overwrite-existing
else
    exec qlever-server -i data/test -j 8 -p 7016 -m 10G -c 5G -e 1G -k 200 -s 30s -a $SPARQL_ACCESS_TOKEN
fi
