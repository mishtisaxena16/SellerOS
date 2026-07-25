"""
engine_bridge.py — locates and exposes the SellerOS Knowledge Engine
(retrieve.py / config.py / embedding.py / chunking.py) to this backend,
without editing any of those files.

Why this exists: the Knowledge Engine and this backend are two
separate projects living as sibling folders on disk —

    Marketsellers/
    ├── SellerOS/                          <- Knowledge Engine
    │   ├── retrieve.py
    │   ├── config.py
    │   ├── embedding.py
    │   └── chunking.py
    └── sellersos_tool_and_agent_layer_1/
        └── backend/                       <- this project
            └── tools/knowledge/knowledge_tool.py

`retrieve.py` does `from config import ...` and `embedding.py` does
`from chunking import ...` — bare, top-level imports that only work if
the SellerOS/ folder itself is on sys.path. Python won't do that
automatically across two separate projects, so this module adds it,
once, before knowledge_tool.py imports `retrieve`.

retrieve.py / config.py / embedding.py / chunking.py are intentionally
left untouched — this file is the only thing that changes.

Path resolution order:
1. `SELLEROS_KNOWLEDGE_ENGINE_PATH` env var (put this in backend/.env)
   — use this if the two projects ever move apart, or get deployed
   separately.
2. Default: the sibling folder layout above, resolved relative to this
   file, matching how the project sits on disk today.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv  # python-dotenv
except ImportError:  # pragma: no cover — dotenv is a soft dependency
    load_dotenv = None

_THIS_FILE = Path(__file__).resolve()

# Load backend/.env (if present) so SELLEROS_KNOWLEDGE_ENGINE_PATH, or
# any future connector credentials read elsewhere, are picked up
# automatically without every entrypoint needing its own load_dotenv()
# call. Safe no-op if python-dotenv isn't installed or no .env exists.
if load_dotenv is not None:
    _backend_env = _THIS_FILE.parents[2] / ".env"  # tools/knowledge -> tools -> backend
    if _backend_env.exists():
        load_dotenv(_backend_env)


def _default_engine_path() -> Path:

    current = _THIS_FILE

    for parent in current.parents:

        retrieve_file = parent / "retrieve.py"
        config_file = parent / "config.py"

        if retrieve_file.exists() and config_file.exists():
            return parent

    raise FileNotFoundError(
        "Could not locate SellerOS Knowledge Engine "
        "(retrieve.py + config.py)."
    )


def resolve_engine_path() -> Path:
    override = os.getenv("SELLEROS_KNOWLEDGE_ENGINE_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return _default_engine_path()


def ensure_on_path() -> Path:
    """
    Adds the Knowledge Engine folder to sys.path if it isn't already
    there, and returns the resolved path. Safe to call more than once
    (e.g. once from knowledge_tool.py, once from a test script) — only
    inserts once.
    """
    engine_path = resolve_engine_path()

    if not engine_path.exists():
        raise FileNotFoundError(
            f"SellerOS Knowledge Engine not found at '{engine_path}'. "
            f"Either restore the sibling-folder layout (SellerOS/ next to "
            f"sellersos_tool_and_agent_layer_1/) or set "
            f"SELLEROS_KNOWLEDGE_ENGINE_PATH in backend/.env to point at it."
        )

    engine_str = str(engine_path)
    if engine_str not in sys.path:
        # Insert at the front so SellerOS/config.py, retrieve.py, etc.
        # are found before any same-named module elsewhere on the path.
        sys.path.insert(0, engine_str)

    return engine_path
