"""Shared pytest fixtures for the Memory Layer test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow `import memory` when running pytest from the `backend/` directory
# or from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.storage import InMemoryStorage  # noqa: E402


@pytest.fixture
def storage() -> InMemoryStorage:
    """A fresh, empty in-memory storage backend for each test."""
    return InMemoryStorage()
