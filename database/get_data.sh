#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="https://sparql.dblp.org/sparql"
LIMIT=100000
MAX_OFFSET=10000000
STREAMS_FILE="streams.txt"
WORKSHOP_STREAMS_FILE="workshop_streams.txt"

# Paginate one query template for one stream.
#   $1 = template file, $2 = short name (used in filenames), $3 = stream URI
run_query () {
  local template="$1"
  local name="$2"
  local stream="$3"
  local stream_safe
  stream_safe=$(printf '%s' "$stream" | tr -c 'A-Za-z0-9' '_')

  local OFFSET
  for (( OFFSET=0; OFFSET<=MAX_OFFSET; OFFSET+=LIMIT )); do
    echo "  [$name] $stream  OFFSET=$OFFSET"
    local QUERY
    QUERY=$(sed \
      -e "s|__STREAM__|$stream|g" \
      -e "s/__LIMIT__/$LIMIT/g" \
      -e "s/__OFFSET__/$OFFSET/g" \
      "$template")

    local OUT="${DATA_PATH}/chunks/${name}_${stream_safe}_${OFFSET}.nt"
    curl -G \
      --create-dirs \
      --retry 5 \
      --retry-delay 10 \
      -H "Accept: application/n-triples" \
      --data-urlencode "query=$QUERY" \
      "$ENDPOINT" \
      -o "$OUT"

    # Stop this stream/query type once a page comes back empty.
    if [ ! -s "$OUT" ]; then
      rm -f "$OUT"
      break
    fi
  done
}

# Read streams.txt: skip blank lines, strip Windows CRs.
while IFS= read -r STREAM || [ -n "$STREAM" ]; do
  STREAM=$(printf '%s' "$STREAM" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
  [ -z "$STREAM" ] && continue

  echo "=== Stream: $STREAM ==="
  run_query add_publications_from_stream.rq publications "$STREAM"
  run_query add_authors_from_stream.rq      authors      "$STREAM"
  run_query add_editors_from_stream.rq      editors      "$STREAM"
  run_query add_signatures_from_stream.rq   signatures   "$STREAM"
  run_query add_stream.rq                   stream       "$STREAM"
done < "$STREAMS_FILE"

# Read workshop_streams.txt: skip blank lines, strip Windows CRs.
while IFS= read -r STREAM || [ -n "$STREAM" ]; do
  STREAM=$(printf '%s' "$STREAM" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
  [ -z "$STREAM" ] && continue

  echo "=== WORKSHOP: $STREAM ==="
  run_query add_publications_from_stream.rq publications "$STREAM"
  run_query add_authors_from_stream.rq      authors      "$STREAM"
  run_query add_editors_from_stream.rq      editors      "$STREAM"
  run_query add_signatures_from_stream.rq   signatures   "$STREAM"
  run_query add_workshop_stream.rq          workshop     "$STREAM"
done < "$WORKSHOP_STREAMS_FILE"

# Combine everything. sort -u removes duplicate triples that appear
# because the same author/editor shows up across many publications.
sort -u ${DATA_PATH}/chunks/*.nt > ${DATA_PATH}/full_dump.nt
echo "Done. $(wc -l < full_dump.nt) triples in full_dump.nt"