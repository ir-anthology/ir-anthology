#!/usr/bin/env sh
rebuild=$1
echo $rebuild
set -e
if [ $rebuild = true ] ; then
    qlever get-data
else
    qlever index --overwrite-existing
    exec qlever-server -i data/test -j 24 -p 7016 -m 10G -c 30G -e 1G -k 1000 -s 60s -a $SPARQL_ACCESS_TOKEN
fi
