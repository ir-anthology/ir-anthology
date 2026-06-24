from datetime import datetime, timezone
from pathlib import Path
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


def list_patches() -> list[str]:
    if not PATCHES_DIR.exists():
        return []
    return sorted(p.name for p in PATCHES_DIR.glob("*.nt"))


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
