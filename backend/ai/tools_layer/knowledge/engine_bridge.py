"""
engine_bridge.py — locates and exposes the SellerOS Knowledge Engine
(retrieve.py / config.py / embedding.py / chunking.py) to this backend,
without editing any of those files.

Why this exists: the Knowledge Engine lives in its own subtree —
currently ai/knowledge_layer/knowledge_engine/ — separate from this
file's own subtree (ai/tools_layer/knowledge/). `retrieve.py` does
`from config import ...` and `embedding.py` does `from chunking import
...` — bare, top-level imports that only work if the Knowledge
Engine's own folder is on sys.path. Python won't do that
automatically across separate subtrees, so this module adds it, once,
before knowledge_tool.py imports `retrieve`.

This project's layout has already moved twice (sibling repos ->
nested-under-backend -> the current numbered-then-renamed ai/*_layer/
structure) — so path resolution here deliberately doesn't hardcode a
fixed relative depth; see _default_engine_path()'s two-phase search
(ancestors, then sibling subtrees) below.

retrieve.py / config.py / embedding.py / chunking.py are intentionally
left untouched — this file is the only thing that changes.

Path resolution order:
1. `SELLEROS_KNOWLEDGE_ENGINE_PATH` env var (put this in SellerOS/.env)
   — use this if the Knowledge Engine ever moves somewhere this
   search genuinely can't find it (e.g. a separate deployment).
2. Default: search this file's ancestors, then sibling subtrees, for
   a directory containing both retrieve.py and config.py.
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


def _find_dotenv() -> Path | None:
    """.env has moved before and will probably move again — search
    ancestors for it instead of hardcoding a parents[N] depth that
    silently goes stale on the next reorg."""
    for parent in _THIS_FILE.parents:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return None


# Load .env (if present) so SELLEROS_KNOWLEDGE_ENGINE_PATH, or any
# future connector credentials read elsewhere, are picked up
# automatically without every entrypoint needing its own load_dotenv()
# call. Safe no-op if python-dotenv isn't installed or no .env exists.
if load_dotenv is not None:
    _dotenv_path = _find_dotenv()
    if _dotenv_path is not None:
        load_dotenv(_dotenv_path)


def _default_engine_path() -> Path:
    current = _THIS_FILE

    # Phase 1: strict ancestors (handles a flatter layout where the
    # Knowledge Engine sits directly above this file).
    for parent in current.parents:
        retrieve_file = parent / "retrieve.py"
        config_file = parent / "config.py"
        if retrieve_file.exists() and config_file.exists():
            return parent

    # Phase 2: sibling subtrees. Under the current layout, this file
    # lives at ai/tools_layer/knowledge/engine_bridge.py while the
    # Knowledge Engine lives at ai/knowledge_layer/knowledge_engine/ —
    # a cousin directory, not an ancestor, so Phase 1 alone can't find
    # it. Search downward from each ancestor instead, stopping at the
    # first ancestor that actually contains a match so this doesn't
    # scan more of the tree than necessary (and never scans past a
    # reasonably project-scoped ancestor — 6 levels up is already well
    # past "backend/" in every layout this project has used so far).
    for ancestor in list(current.parents)[:6]:
        for retrieve_file in ancestor.glob("**/retrieve.py"):
            if (retrieve_file.parent / "config.py").exists():
                return retrieve_file.parent

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
