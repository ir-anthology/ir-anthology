#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="https://sparql.dblp.org/sparql"
LIMIT=100000
MAX_OFFSET=10000000
STREAMS_FILE="streams.txt"
WORKSHOP_STREAMS_FILE="workshop_streams.txt"

add_display_year () {
  local template="get_proceedings_titles_from_stream.rq"
  local name="display_year"
  local stream="$1"
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

    local OUT="${DATA_PATH}/chunks/proceedings_titles_${stream_safe}_${OFFSET}.nt.temp"
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

  # No proceedings found for this stream — nothing to do.
  local tempfiles=( "${DATA_PATH}/chunks/proceedings_titles_${stream_safe}_"*.nt.temp )
  [ -e "${tempfiles[0]}" ] || return 0

  local complete="${DATA_PATH}/chunks/proceedings_titles_${stream_safe}_complete.nt.temp"
  sort -u "${tempfiles[@]}" > "$complete"


  # For each N-Triple "<pub> <predicate> "title" .", extract the 4-digit year from the title and emit a yearOfConference triple.
  sed -En 's|^(<[^>]+>) <[^>]+> ".*([12][0-9]{3})[^"]*".*|\1 <https://ir.webis.de/kg#yearOfConference> "\2" .|p' \
    "$complete" > "${DATA_PATH}/chunks/yearOfConference_${stream_safe}.nt"
  rm -f "${DATA_PATH}/chunks/"*.nt.temp
}

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
  add_display_year "$STREAM"
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
  add_display_year "$STREAM"
done < "$WORKSHOP_STREAMS_FILE"

patch_files=( "$DATA_PATH/patches/"*.nt )
if [ -e "${patch_files[0]}" ]; then
  echo "Merging ${#patch_files[@]} patch file(s)..."
  triple_count=$(sort -u "${DATA_PATH}/chunks/"*.nt "${patch_files[@]}" | wc -l)
else
  triple_count=$(sort -u "${DATA_PATH}/chunks/"*.nt | wc -l)
fi
echo "Done. $triple_count triples total."