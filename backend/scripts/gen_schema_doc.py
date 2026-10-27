#!/usr/bin/env python3
"""Regenerates the "Worked examples" section of ../SCHEMA.md from sparqlTemplates.py.

Keeps the generated section honest without hand-maintenance: it imports
sparqlTemplates as a plain module (safe — pure string constants, no side effects,
no network calls) so every example is the actual, already-composed query string a
route handler sends to QLever, and it derives each example's "used by" caption by
scanning main.py's real route decorators rather than from a hand-kept map, so the
caption can't drift from the routing table the way hand-written prose can.

Run whenever sparqlTemplates.py changes:

    python backend/scripts/gen_schema_doc.py

Only rewrites the text between the START/END markers in SCHEMA.md; everything
else in the file (mental model, gotchas, class/property tables, verification
recipe) is hand-authored and left untouched.
"""
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
import sparqlTemplates  # noqa: E402

SCHEMA_MD = BACKEND_DIR / "SCHEMA.md"
MAIN_PY = BACKEND_DIR / "main.py"

START_MARKER = "<!-- GENERATED:EXAMPLES START -->"
END_MARKER = "<!-- GENERATED:EXAMPLES END -->"

# Shared string fragments composed into the *_TABLE_TEMPLATE constants at import
# time (see sparqlTemplates.py) — not queries in their own right, skip them.
_INTERNAL_NAMES = {"_ENTITY_TABLE_BODY", "_ENTITY_TABLE_PREFIXES"}

_DECORATOR_RE = re.compile(r'^@app\.(get|post|delete|put)\("([^"]+)"\)', re.MULTILINE)
_TEMPLATE_REF_RE = re.compile(r'sparqlTemplates\.([A-Z_]+)')
# The four entity-table routes no longer name their templates: they delegate to
# main._entity_table("<Entity>", ...), which looks the templates up in
# sparqlTemplates.TABLES. Resolve those through the registry instead.
_ENTITY_TABLE_RE = re.compile(r'_entity_table\("(\w+)"')


def _template_name_by_value() -> dict[str, str]:
    """Reverse map a template's text back to its constant name."""
    return {v: k for k, v in vars(sparqlTemplates).items()
            if k.isupper() and k.endswith("TEMPLATE") and isinstance(v, str)}


def find_routes(main_py_source: str) -> dict[str, list[str]]:
    """Map each sparqlTemplates.NAME to the route(s) whose handler references it.

    Splits main.py into blocks starting at each `@app.<verb>("<path>")` decorator
    and scans each block (up to the next decorator, or EOF) for
    `sparqlTemplates.NAME` references.
    """
    by_value = _template_name_by_value()
    matches = list(_DECORATOR_RE.finditer(main_py_source))
    routes: dict[str, list[str]] = {}
    for i, m in enumerate(matches):
        verb, path = m.group(1).upper(), m.group(2)
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(main_py_source)
        block = main_py_source[m.end():block_end]
        names = list(dict.fromkeys(_TEMPLATE_REF_RE.findall(block)))
        for entity in dict.fromkeys(_ENTITY_TABLE_RE.findall(block)):
            spec = sparqlTemplates.TABLES[entity]
            for template in (spec.template, spec.year_counts_template):
                name = by_value.get(template) if template else None
                if name and name not in names:
                    names.append(name)
        for name in names:
            routes.setdefault(name, []).append(f"{verb} {path}")
    return routes


def render_examples(routes: dict[str, list[str]]) -> str:
    parts = []
    for name, value in vars(sparqlTemplates).items():
        if name in _INTERNAL_NAMES:
            continue
        if not (name.isupper() and name.endswith("TEMPLATE") and isinstance(value, str)):
            continue
        used_by = routes.get(name)
        if used_by:
            caption = f"Used by: `{'`, `'.join(used_by)}`"
        else:
            caption = (
                "**Not referenced by any route in `main.py` at generation time** — "
                "appears unused; verify before treating this as a live query pattern."
            )
        parts.append(f"#### `{name}`\n\n{caption}\n\n```sparql\n{value.strip()}\n```")
    return "\n\n".join(parts)


def main() -> None:
    main_py_source = MAIN_PY.read_text()
    routes = find_routes(main_py_source)
    generated = render_examples(routes)

    schema = SCHEMA_MD.read_text()
    start_i = schema.index(START_MARKER) + len(START_MARKER)
    end_i = schema.index(END_MARKER)
    new_schema = schema[:start_i] + "\n\n" + generated + "\n\n" + schema[end_i:]
    SCHEMA_MD.write_text(new_schema)

    template_count = sum(
        1 for name, v in vars(sparqlTemplates).items()
        if name not in _INTERNAL_NAMES and name.isupper() and name.endswith("TEMPLATE") and isinstance(v, str)
    )
    unmapped = template_count - len(routes)
    print(f"Regenerated {template_count} templates ({len(routes)} route-mapped, {unmapped} unmapped) -> {SCHEMA_MD}")


if __name__ == "__main__":
    main()
