"""
Tests for KnowledgeTool.search() -- the RAG pipeline (Ollama query
embedding -> ChromaDB vector search -> context assembly).

Converted from a bare script (module-level `asyncio.run(main())`,
executed at import time) to skip-guarded pytest tests, for the same
reason as test_embedding.py: a live-Ollama dependency shouldn't be
able to fail collection for the whole suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ai.tools_layer.base.tool_context import ToolContext  # noqa: E402
from backend.ai.tools_layer.knowledge.engine_bridge import ensure_on_path  # noqa: E402
from backend.ai.tools_layer.knowledge.knowledge_tool import KnowledgeTool  # noqa: E402
from conftest import ollama_is_running  # noqa: E402

ensure_on_path()
from config import OLLAMA_HOST  # noqa: E402

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not ollama_is_running(OLLAMA_HOST),
        reason=f"Ollama server not reachable at {OLLAMA_HOST}",
    ),
]


@pytest.fixture
def tool() -> KnowledgeTool:
    return KnowledgeTool()


@pytest.fixture
def context() -> ToolContext:
    return ToolContext(seller_id="test_seller", platform="amazon")


async def test_search_returns_a_successful_tool_result(tool, context):
    result = await tool.search(
        context=context,
        query="What is Amazon account health?",
    )

    assert result.success is True
    assert isinstance(result.message, str) and result.message


async def test_search_result_metadata_includes_chunks_and_query(tool, context):
    result = await tool.search(
        context=context,
        query="What is Amazon account health?",
    )

    assert "query" in result.metadata
    assert result.metadata["query"] == "What is Amazon account health?"
    assert "chunks" in result.metadata
    assert isinstance(result.metadata["chunks"], list)


async def test_search_requires_a_nonempty_query(tool, context):
    result = await tool.search(context=context, query="")

    assert result.success is False
    assert result.error == "VALIDATION_ERROR"
