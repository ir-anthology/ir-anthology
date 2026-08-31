from datetime import datetime, timezone
from pathlib import Path
import json
import os

_data_path = os.environ.get("DATA_PATH")
PATCHES_DIR = Path(_data_path) / "patches" if _data_path else Path(__file__).parent.parent / "data" / "patches"


def save_patch(slug: str, nt_content: str) -> str:
    """Write N-Triples to a timestamped patch file. Returns the filename."""
    PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    # Sanitise slug so it's safe as a filename
    safe_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in slug)
    filename = f"{ts}_{safe_slug}.nt"
    (PATCHES_DIR / filename).write_text(nt_content.strip() + "\n", encoding="utf-8")
    return filename


def save_patch_meta(filename: str, meta: dict) -> None:
    stem = filename.removesuffix(".nt")
    (PATCHES_DIR / f"{stem}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def patch_exists(filename: str) -> bool:
    path = PATCHES_DIR / filename
    return path.exists() and path.parent == PATCHES_DIR


def read_patch_meta(filename: str) -> dict | None:
    stem = filename.removesuffix(".nt")
    path = PATCHES_DIR / f"{stem}.meta.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_patches() -> list[dict]:
    if not PATCHES_DIR.exists():
        return []
    names = sorted(p.name for p in PATCHES_DIR.glob("*.nt"))
    return [{"filename": n, **(read_patch_meta(n) or {})} for n in names]


def read_patch(filename: str) -> str:
    path = PATCHES_DIR / filename
    if not path.exists() or path.parent != PATCHES_DIR:
        raise FileNotFoundError(filename)
    return path.read_text(encoding="utf-8")


def nt_to_sparql_insert(nt_content: str) -> str:
    """Wrap N-Triples lines in a SPARQL INSERT DATA block."""
    triples = "\n".join(
        line for line in nt_content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    return f"INSERT DATA {{\n{triples}\n}}"


def nt_to_sparql_delete(nt_content: str) -> str:
    """Wrap N-Triples lines in a SPARQL DELETE DATA block — reverses nt_to_sparql_insert
    exactly, since the patch file preserves the verbatim triples that were inserted."""
    triples = "\n".join(
        line for line in nt_content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    return f"DELETE DATA {{\n{triples}\n}}"


def delete_patch_files(filename: str) -> None:
    """Remove a patch's .nt file and its .meta.json sidecar."""
    path = PATCHES_DIR / filename
    if not path.exists() or path.parent != PATCHES_DIR:
        raise FileNotFoundError(filename)
    path.unlink()
    meta_path = PATCHES_DIR / f"{filename.removesuffix('.nt')}.meta.json"
    meta_path.unlink(missing_ok=True)
