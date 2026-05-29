#!/usr/bin/env bash

set -euo pipefail

ENDPOINT="https://sparql.dblp.org/sparql"

LIMIT=100000
MAX_OFFSET=10000000

mkdir -p chunks

for (( OFFSET=0; OFFSET<=MAX_OFFSET; OFFSET+=LIMIT ))
do
  echo "Exporting OFFSET=$OFFSET"

  QUERY=$(sed \
    -e "s/__LIMIT__/$LIMIT/g" \
    -e "s/__OFFSET__/$OFFSET/g" \
    query.rq)

  curl -G \
    --retry 5 \
    --retry-delay 10 \
    -H "Accept: application/n-triples" \
    --data-urlencode "query=$QUERY" \
    "$ENDPOINT" \
    -o "chunks/chunk_${OFFSET}.nt"

  # Stop if empty result
  if [ ! -s "chunks/chunk_${OFFSET}.nt" ]; then
    echo "No more results."
    rm "chunks/chunk_${OFFSET}.nt"
    break
  fi

done

cat chunks/*.nt > full_dump.nt

rm -r chunks

echo "Done."
