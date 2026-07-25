"""Shared pytest fixtures for the Memory Layer test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def _find_memory_layer_dir() -> Path:
    # tests/ used to sit directly inside memory_layer/ (making
    # parent.parent = memory_layer/); it's now a top-level SellerOS/tests/
    # folder covering multiple layers, while memory_layer/ itself moved
    # to backend/ai/memory_layer/. Search instead of hardcoding a depth
    # that's already changed once and will likely change again.
    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        for candidate in ancestor.glob("**/memory_layer"):
            if (candidate / "memory" / "service.py").exists():
                return candidate
    raise FileNotFoundError(
        "Could not locate memory_layer/ (expected memory/service.py inside it) "
        "near tests/conftest.py."
    )


# Allow `import memory` regardless of where memory_layer/ currently lives.
sys.path.insert(0, str(_find_memory_layer_dir()))

from memory.storage import InMemoryStorage  # noqa: E402


@pytest.fixture
def storage() -> InMemoryStorage:
    """A fresh, empty in-memory storage backend for each test."""
    return InMemoryStorage()
