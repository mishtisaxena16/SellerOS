"""
Tests for SellerCoachAgent end-to-end: knowledge_tool.search() -> LLM
reasoning via OllamaReasoner. Converted from a bare script (module-level
`asyncio.run(main())`) to skip-guarded pytest tests -- see
test_embedding.py for why.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ai.agent_layer.base.reasoning import OllamaReasoner  # noqa: E402
from backend.ai.agent_layer.base.tool_manager import ToolManager  # noqa: E402
from backend.ai.agent_layer.seller_coach.coach_agent import SellerCoachAgent  # noqa: E402
from backend.ai.tools_layer.registry.tool_registry import build_default_registry  # noqa: E402
from conftest import ollama_is_running  # noqa: E402

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not ollama_is_running(),
        reason="Ollama server not reachable at localhost:11434",
    ),
]


@pytest.fixture
def tool_manager() -> ToolManager:
    registry = build_default_registry()
    return ToolManager(registry=registry, seller_id="test_seller")


async def test_seller_coach_agent_answers_a_question(tool_manager):
    agent = SellerCoachAgent(reasoner=OllamaReasoner())

    result = await agent.run(
        tool_manager=tool_manager,
        seller_id="test_seller",
        user_query="What is Amazon account health?",
    )

    assert result.success is True
    assert isinstance(result.message, str) and result.message.strip()


async def test_seller_coach_agent_result_has_no_confidence_of_zero(tool_manager):
    # AgentResult deliberately uses confidence=None for "not measured"
    # rather than 0.0, specifically so a real answer never looks
    # identical to "very unconfident" -- assert that distinction holds.
    agent = SellerCoachAgent(reasoner=OllamaReasoner())

    result = await agent.run(
        tool_manager=tool_manager,
        seller_id="test_seller",
        user_query="What is Amazon account health?",
    )

    assert result.confidence is None or result.confidence > 0.0
