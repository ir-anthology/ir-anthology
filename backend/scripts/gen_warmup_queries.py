#!/usr/bin/env python3
"""Generate the warm-up/pin queries that database/run_qlever.sh fires at startup.

WHY THIS IS GENERATED AND NOT HAND-WRITTEN: QLever's cache key is the query string
itself. A hand-copied warm-up stops matching the moment anyone edits a template —
and it fails *silently*: it pins a query nobody issues, the landing views stay slow,
and nothing errors. So the queries are rendered from the same constants the backend
substitutes at request time, reusing main.parse_order() and main.build_year_seed()
rather than reimplementing them.

Writes database/warmup/*.rq. Run it after changing sparqlTemplates.py, or when the
data has changed enough that the seeded year-count queries should be refreshed:

    python3 backend/scripts/gen_warmup_queries.py [sparql-endpoint]
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sparqlTemplates as T  # noqa: E402  — now also the query-construction authority

# main.py is NOT imported: it pulls in FastAPI, httpx and ~450 modules for two pure
# functions. Everything needed to compose a query lives in sparqlTemplates.py.
SPARQL_ENDPOINT = "https://database-ir-anthology.srv.webis.de/"

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "database" / "warmup"
TABLE_CONFIG_TS = REPO / "frontend" / "src" / "lib" / "tableConfig.ts"

# TableParams defaults in main.py: page 1, limit 50.
LIMIT, OFFSET = 50, 0

# Output basename per entity. Purely a generator concern (run_qlever.sh globs
# warmup/*.rq, so the names are cosmetic) — everything that actually shapes a query
# now comes from sparqlTemplates.TABLES.
OUTPUT_NAMES = {"Author": "authors", "Venue": "venues", "Year": "years", "Publication": "publications"}

_DEFAULT_SORT_RE = re.compile(r"(\w+):\s*\{\s*sort_by:\s*'([^']+)',\s*order:\s*'([^']+)'\s*\}")


def read_default_sorts() -> dict[str, tuple[str, str]]:
    """Parse ENTITY_DEFAULT_SORT out of the frontend's tableConfig.ts.

    Parsed rather than mirrored because this is the one input that lives in ANOTHER
    part of the repo: a default-sort change in the frontend would otherwise leave the
    warm-up pinning a query the site no longer requests, with nothing to catch it.
    """
    src = TABLE_CONFIG_TS.read_text()
    block = src.split("ENTITY_DEFAULT_SORT", 1)[1].split("};", 1)[0]
    sorts = {m.group(1): (m.group(2), m.group(3)) for m in _DEFAULT_SORT_RE.finditer(block)}
    missing = set(T.TABLES) - set(sorts)
    if missing:
        raise SystemExit(f"could not parse a default sort for {sorted(missing)} from {TABLE_CONFIG_TS}")
    return sorts


def render_table(template: str, sort_by: str, order: str, aliases) -> str:
    """Exactly what main._run_table_page() builds for an unfiltered first page."""
    return T.compose_table_query(
        template,
        filters="",
        order=T.parse_order(sort_by, order, None, aliases),
        limit=LIMIT,
        offset=OFFSET,
    )


def run(endpoint: str, query: str) -> list:
    """POST a query and return its bindings (stdlib only — this runs outside the app)."""
    req = urllib.request.Request(
        endpoint,
        data=urllib.parse.urlencode({"query": query}).encode(),
        headers={"Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)["results"]["bindings"]


def main_() -> int:
    endpoint = sys.argv[1] if len(sys.argv) > 1 else SPARQL_ENDPOINT
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Render everything first and only touch the output directory once it all
    # succeeded — an earlier version deleted the stale files up front and then
    # aborted on a bad alias, leaving no warm-up queries at all.
    rendered: dict[str, str] = {}

    default_sorts = read_default_sorts()

    for entity, spec in T.TABLES.items():
        if entity not in OUTPUT_NAMES:
            raise SystemExit(f"no OUTPUT_NAMES entry for new entity {entity!r} in {Path(__file__).name}")
        name = OUTPUT_NAMES[entity]
        sort_by, order = default_sorts[entity]
        table_query = render_table(spec.template, sort_by, order, spec.sort_aliases)
        rendered[f"{name}.rq"] = table_query

        if spec.year_counts_template is None:
            continue
        # The year-count query main._merge_year_counts() issues is seeded with the
        # URIs of the page it just fetched, so the table query has to be run to build
        # it. Bake the seed for page 1 — the same rows the landing view shows.
        seed = T.build_year_seed(entity, run(endpoint, table_query))
        if seed is None:
            print(f"  !! {name}: no seedable URIs, skipping year counts")
            continue
        rendered[f"{name}-years.rq"] = spec.year_counts_template.replace("$SEED", seed).replace("$FILTERS", "")

    for stale in OUT_DIR.glob("*.rq"):
        if stale.name not in rendered:
            stale.unlink()
    for filename, text in sorted(rendered.items()):
        (OUT_DIR / filename).write_text(text)
        print(f"  {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_())
