#!/usr/bin/env sh
rebuild=$1
echo $rebuild
set -e
if [ "$rebuild" = true ] ; then
    qlever get-data
else
    qlever index --overwrite-existing

    # Warm up and pin the queries the landing views actually issue, so the first
    # visitor after a restart does not pay the cold-query cost (measured: up to 37s
    # for the publications table). Backgrounded BEFORE the exec and polling until the
    # server answers — exec replaces this shell with qlever-server, so the server
    # stays PID 1 and receives SIGTERM directly, while this subshell survives as an
    # independent process. Placed after 'qlever index' on purpose: indexing is
    # synchronous and can take minutes, so the poll only waits out server startup.
    #
    # The .rq files are GENERATED from backend/sparqlTemplates.py by
    # backend/scripts/gen_warmup_queries.py — do NOT hand-edit them. QLever's cache
    # key is the exact query string, so a copy that drifts from the templates pins
    # queries nobody issues and the landing views stay slow with no error at all.
    ( until curl -sf localhost:7016 -d cmd=cache-stats >/dev/null 2>&1; do sleep 2; done
      for f in warmup/*.rq; do
          [ -e "$f" ] || continue
          curl -s localhost:7016 --data-urlencode query@"$f" \
               --data pin-subresults=true --data send=0 \
               --data access-token="$SPARQL_ACCESS_TOKEN" >/dev/null
      done
    ) &

    exec qlever-server -i data/test -j 24 -p 7016 -m 50G -c 25G -e 1G -k 500000 -s 60s -a $SPARQL_ACCESS_TOKEN --enable-metrics
fi
