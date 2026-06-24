#!/usr/bin/env bash
# Replay all patches in database/patches/ against the live SPARQL endpoint.
# Used after a database re-index to restore manually added data.
#
# Required env vars:
#   DATA_PATH            same value used in get_data.sh (e.g. /path/to/data)
#   SPARQL_ENDPOINT      e.g. https://database-ir-anthology.srv.webis.de/
#   SPARQL_ACCESS_TOKEN  QLever access token (from Qleverfile)
set -euo pipefail

ENDPOINT="${SPARQL_ENDPOINT:-https://database-ir-anthology.srv.webis.de/}"
ACCESS_TOKEN="${SPARQL_ACCESS_TOKEN:-}"
PATCHES_DIR="${DATA_PATH}/patches"

shopt -s nullglob
patches=("$PATCHES_DIR"/*.nt)

if [ ${#patches[@]} -eq 0 ]; then
    echo "No patches to apply."
    exit 0
fi

URL="$ENDPOINT"
[ -n "$ACCESS_TOKEN" ] && URL="${URL}?access-token=${ACCESS_TOKEN}"

for patch in "${patches[@]}"; do
    echo "Applying $(basename "$patch")..."
    triples=$(cat "$patch")
    curl -sf -X POST "$URL" \
        -H "Content-Type: application/sparql-update" \
        --data-raw "INSERT DATA {
$triples
}"
    echo " ok"
done

echo "Done. Applied ${#patches[@]} patch(es)."
