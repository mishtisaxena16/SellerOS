"""
memory_bridge.py — makes `import memory` (the Memory Layer package)
work from anywhere in backend/, without moving or renaming any file
inside the package itself.

Why this exists: the Memory Layer package lives at
`backend/memory_layer/memory/` — one level deeper than every other
top-level package in this backend (agent_layer/, tools/, connectors/,
models/), because `memory_layer/` also holds the package's own
`tests/`, `pytest.ini`, and `requirements.txt` alongside the actual
`memory/` package. That's a perfectly reasonable layout for the
package's own test suite (its conftest.py already does the same
sys.path trick — see memory_layer/tests/conftest.py), but it means
`from memory.service import MemoryService` doesn't work from
orchestrator.py or supervisor.py without `memory_layer/` itself being
on sys.path first.

(The directory used to be named "memory layer" with a space, which is
not a valid Python identifier and breaks dotted imports outright —
renamed to memory_layer/ as part of this integration pass.)
"""
from __future__ import annotations

import sys
from pathlib import Path

_MEMORY_LAYER_DIR = Path(__file__).resolve().parent / "memory_layer"


def ensure_on_path() -> Path:
    if not _MEMORY_LAYER_DIR.exists():
        raise FileNotFoundError(
            f"Memory Layer package not found at '{_MEMORY_LAYER_DIR}'. "
            f"Expected backend/memory_layer/memory/service.py to exist."
        )
    path_str = str(_MEMORY_LAYER_DIR)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    return _MEMORY_LAYER_DIR
