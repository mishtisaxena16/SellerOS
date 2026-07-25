"""
memory_bridge.py — makes `import memory` (the Memory Layer package)
work from anywhere in this backend, without moving or renaming any
file inside the package itself.

Why this exists: the Memory Layer package lives at
`.../memory_layer/memory/`, alongside this file's own directory
(memory_bridge.py sits directly inside memory_layer/, next to
memory/, tests/, pytest.ini, and requirements.txt) — one level deeper
than most other layer packages, because memory_layer/ also holds the
package's own bundled test suite. That's a fine layout for the
package's own tests (memory_layer/tests/conftest.py does the same
sys.path trick), but it means `from memory.service import
MemoryService` doesn't work from orchestrator.py or supervisor.py
without memory_layer/ itself being on sys.path first.

This directory has already moved twice — "memory layer" (a space,
which isn't a valid Python identifier at all) -> memory_layer/ next to
orchestrator.py -> its current location nested under ai/ — so rather
than hardcode "this file's parent, then descend into a child named
memory_layer" (correct once, broken the next time this gets moved),
_find_memory_layer_dir() below just checks this file's own directory
first (correct today) and falls back to searching nearby for
memory/service.py if that ever stops being true.
"""
from __future__ import annotations

import sys
from pathlib import Path

_THIS_FILE = Path(__file__).resolve()


def _find_memory_layer_dir() -> Path:
    # Phase 1: this file's own directory — correct for the current
    # layout, where memory_bridge.py sits right next to memory/.
    here = _THIS_FILE.parent
    if (here / "memory" / "service.py").exists():
        return here

    # Phase 2: fallback search, in case memory_bridge.py itself ever
    # moves elsewhere while memory/ stays put (mirrors engine_bridge.py's
    # two-phase approach for the same reason).
    for ancestor in list(_THIS_FILE.parents)[:6]:
        for candidate in ancestor.glob("**/memory/service.py"):
            return candidate.parent.parent

    raise FileNotFoundError(
        "Memory Layer package not found — expected a memory/service.py "
        "somewhere near memory_bridge.py."
    )


_MEMORY_LAYER_DIR = _find_memory_layer_dir()


def ensure_on_path() -> Path:
    path_str = str(_MEMORY_LAYER_DIR)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    return _MEMORY_LAYER_DIR
