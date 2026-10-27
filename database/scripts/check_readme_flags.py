#!/usr/bin/env python3
"""Fail if README.md's entrypoint flag table disagrees with run_qlever.sh.

That table has drifted twice already (it exists because of a code-review finding
that it had diverged in the first place), and the drift is invisible: the server
runs fine on the real flags while the docs describe different ones. Stdlib only and
offline, so CI needs no setup.

    python3 database/scripts/check_readme_flags.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RUN_SH = HERE / "run_qlever.sh"
README = HERE / "README.md"

# Flags intentionally absent from the table (none today; listed so adding one is a
# deliberate edit rather than a silent omission).
UNDOCUMENTED: set[str] = set()


def flags_from_script() -> dict[str, str | None]:
    # Anchored on the real command: a prose comment in the same file also mentions
    # both "exec" and "qlever-server", and matching loosely picked that up instead.
    line = next((l for l in RUN_SH.read_text().splitlines()
                 if re.match(r"\s*exec\s+qlever-server\b", l)), None)
    if line is None:
        sys.exit(f"{RUN_SH}: no 'exec qlever-server ...' command found")
    tokens = line.split()
    tokens = tokens[tokens.index("qlever-server") + 1:]
    flags: dict[str, str | None] = {}
    i = 0
    while i < len(tokens):
        if tokens[i].startswith("-"):
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                flags[tokens[i]] = tokens[i + 1]
                i += 2
            else:
                flags[tokens[i]] = None  # valueless, e.g. --enable-metrics
                i += 1
        else:
            i += 1
    return flags


_ROW = re.compile(r"^\|\s*`(-{1,2}[A-Za-z][A-Za-z-]*)`\s*\|\s*(.*?)\s*\|", re.MULTILINE)


def flags_from_readme() -> dict[str, str | None]:
    flags: dict[str, str | None] = {}
    for flag, value in _ROW.findall(README.read_text()):
        value = value.strip().strip("`")
        flags[flag] = None if value in {"", "—", "-"} else value
    return flags


def main() -> int:
    script, doc = flags_from_script(), flags_from_readme()
    problems = []
    for flag in sorted(set(script) | set(doc)):
        if flag in UNDOCUMENTED:
            continue
        if flag not in doc:
            problems.append(f"  {flag}: passed as {script[flag]!r} by run_qlever.sh but ABSENT from the README table")
        elif flag not in script:
            problems.append(f"  {flag}: documented as {doc[flag]!r} but NOT passed by run_qlever.sh")
        elif script[flag] != doc[flag]:
            problems.append(f"  {flag}: run_qlever.sh passes {script[flag]!r}, README says {doc[flag]!r}")
    if problems:
        print("database/README.md's entrypoint flag table is out of step with run_qlever.sh:\n")
        print("\n".join(problems))
        print("\nUpdate the table in README.md's 'Docker entrypoint (production)' section.")
        return 1
    print(f"flag table matches run_qlever.sh ({len(script)} flags)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
