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

    python3 backend/scripts/gen_warmup_queries.py [backend-api-base-url]
"""
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sparqlTemplates as T  # noqa: E402  — now also the query-construction authority

# main.py is NOT imported: it pulls in FastAPI, httpx and ~450 modules for two pure
# functions. Everything needed to compose a query lives in sparqlTemplates.py.

# The PUBLIC backend API, not the QLever endpoint behind it. The seeded year-count
# queries need the URIs on page 1, and the table API already returns them in exactly
# the shape build_year_seed() consumes — while the raw SPARQL endpoint
# (database-ir-anthology.srv.webis.de) sits in an internal zone that GitHub's hosted
# runners cannot reach, which is what broke the first CI run of this script.
BACKEND_ENDPOINT = "https://backend-ir-anthology.web.webis.de/api/"

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
_ENDPOINT_RE = re.compile(r"(\w+):\s*'([^']+)'")


def read_endpoints() -> dict[str, str]:
    """Parse ENTITY_ENDPOINTS out of the frontend's tableConfig.ts.

    Same reasoning as read_default_sorts(): this mapping lives in the frontend, so
    parsing it beats mirroring it. Keeping both reads in one file also means the
    accepted frontend dependency stays a single, visible one.
    """
    block = TABLE_CONFIG_TS.read_text().split("ENTITY_ENDPOINTS", 1)[1].split("};", 1)[0]
    endpoints = dict(_ENDPOINT_RE.findall(block))
    missing = set(T.TABLES) - set(endpoints)
    if missing:
        raise SystemExit(f"no endpoint for {sorted(missing)} in {TABLE_CONFIG_TS}")
    return endpoints


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


def warn(message: str) -> None:
    """Loud on a CI log, plain locally. Never silent — a skipped warm-up is the kind
    of thing that otherwise goes unnoticed until the site is slow."""
    prefix = "::warning::" if os.environ.get("GITHUB_ACTIONS") else "WARNING: "
    print(f"{prefix}{message}", file=sys.stderr)


def reachable(endpoint: str, timeout: float = 5.0) -> bool:
    """Cheap TCP pre-flight.

    The seeded year-count queries need a live SPARQL endpoint, and GitHub's hosted
    runners cannot reach the webis one — the port is filtered, so a plain request sits
    there until the OS connect timeout (observed: 2m14s) and then fails the build.
    Probe first and fail in seconds instead.
    """
    parsed = urllib.parse.urlparse(endpoint)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout):
            return True
    except OSError:
        return False


class PageUnavailable(Exception):
    """Any reason page 1 could not be fetched — unreachable host, HTTP error,
    timeout, malformed body. All of them mean the same thing here: no seed."""


def fetch_page(base: str, path: str, sort_by: str, order: str) -> list:
    """Page 1 of one entity table, straight from the public API."""
    query = urllib.parse.urlencode(
        {"sort_by": sort_by, "order": order, "page": 1, "limit": LIMIT})
    url = f"{base.rstrip('/')}/{path}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            bindings = json.load(resp)["bindings"]
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        raise PageUnavailable(f"{url}: {exc}") from exc
    if not bindings:
        raise PageUnavailable(f"{url}: no rows returned")
    return bindings


def main_() -> int:
    endpoint = sys.argv[1] if len(sys.argv) > 1 else BACKEND_ENDPOINT
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Render everything first and only touch the output directory once it all
    # succeeded — an earlier version deleted the stale files up front and then
    # aborted on a bad alias, leaving no warm-up queries at all.
    rendered: dict[str, str] = {}

    default_sorts = read_default_sorts()
    endpoints = read_endpoints()

    # The four table queries render offline. Only the seeded year-count ones need the
    # endpoint, and by measurement they are worth ~0.9s of cold latency against the
    # ~45s the table queries cover — so an unreachable endpoint degrades the warm-up
    # rather than failing the build.
    seeds_possible = reachable(endpoint)
    if not seeds_possible:
        warn(f"{endpoint} is unreachable — generating the table warm-up queries only, "
             "without the seeded year-count ones (costs ~0.9s of first-visit latency)")

    for entity, spec in T.TABLES.items():
        if entity not in OUTPUT_NAMES:
            raise SystemExit(f"no OUTPUT_NAMES entry for new entity {entity!r} in {Path(__file__).name}")
        name = OUTPUT_NAMES[entity]
        sort_by, order = default_sorts[entity]
        table_query = render_table(spec.template, sort_by, order, spec.sort_aliases)
        rendered[f"{name}.rq"] = table_query

        if spec.year_counts_template is None or not seeds_possible:
            continue
        # The year-count query main._merge_year_counts() issues is seeded with the
        # URIs of the page it just fetched, so the table query has to be run to build
        # it. Bake the seed for page 1 — the same rows the landing view shows.
        try:
            bindings = fetch_page(endpoint, endpoints[entity], sort_by, order)
        except PageUnavailable as exc:
            seeds_possible = False
            warn(f"could not fetch page 1 for {entity} ({exc}) — skipping the seeded "
                 "year-count warm-up queries (costs ~0.9s of first-visit latency)")
            continue
        seed = T.build_year_seed(entity, bindings)
        if seed is None:
            warn(f"{entity}: page 1 contained no seedable URIs — skipping its year counts")
            continue
        rendered[f"{name}-years.rq"] = spec.year_counts_template.replace("$SEED", seed).replace("$FILTERS", "")

    for stale in OUT_DIR.glob("*.rq"):
        if stale.name not in rendered:
            stale.unlink()
    for filename, text in sorted(rendered.items()):
        (OUT_DIR / filename).write_text(text)
        print(f"  {filename}")
    if not seeds_possible:
        print("  (year-count warm-up queries skipped — see the warning above)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_())
