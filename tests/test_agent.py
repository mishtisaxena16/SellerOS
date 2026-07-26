import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from backend.ai.agent_layer.seller_coach.coach_agent import SellerCoachAgent
from backend.ai.agent_layer.base.reasoning import OllamaReasoner
from backend.ai.agent_layer.base.tool_manager import ToolManager

from backend.ai.tools_layer.registry.tool_registry import build_default_registry


async def main():

    registry = build_default_registry()

    tool_manager = ToolManager(
        registry=registry,
        seller_id="test_seller"
    )

    reasoner = OllamaReasoner()

    agent = SellerCoachAgent(
        reasoner=reasoner
    )

    result = await agent.run(
        tool_manager=tool_manager,
        seller_id="test_seller",
        user_query="What is Amazon account health?"
    )

    print(result)


asyncio.run(main())