"""
Tests for the Knowledge Engine's embedding generation via Ollama.

This used to be a bare script (module-level code, no `def test_...`)
that called a live Ollama server the moment pytest imported the file,
which failed the *entire collection step* whenever Ollama wasn't
running -- not just this file's own tests. Converted to real,
skip-guarded pytest tests: they run for real against Ollama when it's
reachable, and skip cleanly (not error) when it isn't.

Also fixed: the original script hardcoded "qwen3-embedding:0.6b",
which doesn't match the model the app actually configures
(EMBEDDING_MODEL = "nomic-embed-text" in knowledge_engine/config.py) --
so even when it passed, it wasn't testing the real pipeline. This now
imports EMBEDDING_MODEL/OLLAMA_HOST from that config directly, via the
same engine_bridge.ensure_on_path() the app itself uses to resolve the
Knowledge Engine's location.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ai.tools_layer.knowledge.engine_bridge import ensure_on_path  # noqa: E402
from conftest import ollama_is_running  # noqa: E402

ensure_on_path()
from config import EMBEDDING_MODEL, OLLAMA_HOST  # noqa: E402

pytestmark = pytest.mark.skipif(
    not ollama_is_running(OLLAMA_HOST),
    reason=f"Ollama server not reachable at {OLLAMA_HOST}",
)


@pytest.fixture(scope="module")
def ollama_client():
    from ollama import Client
    return Client(host=OLLAMA_HOST)


def test_embedding_returns_a_nonempty_float_vector(ollama_client):
    response = ollama_client.embeddings(
        model=EMBEDDING_MODEL,
        prompt="What is Amazon account health?",
    )
    embedding = response["embedding"]

    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, (int, float)) for x in embedding)


def test_embedding_is_deterministic_for_the_same_input(ollama_client):
    prompt = "What is Amazon account health?"
    first = ollama_client.embeddings(model=EMBEDDING_MODEL, prompt=prompt)["embedding"]
    second = ollama_client.embeddings(model=EMBEDDING_MODEL, prompt=prompt)["embedding"]

    assert first == second


def test_different_prompts_produce_different_embeddings(ollama_client):
    a = ollama_client.embeddings(
        model=EMBEDDING_MODEL, prompt="What is Amazon account health?"
    )["embedding"]
    b = ollama_client.embeddings(
        model=EMBEDDING_MODEL, prompt="How do I file GST returns?"
    )["embedding"]

    assert a != b
