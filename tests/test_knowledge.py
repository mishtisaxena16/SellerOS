# test_knowledge.py

import asyncio
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from ai.tools_layer.knowledge.knowledge_tool import KnowledgeTool
from ai.tools_layer.base.tool_context import ToolContext


async def main():

    tool = KnowledgeTool()

    context = ToolContext(
        seller_id="test_seller",
        platform="amazon"
    )

    print(inspect.signature(tool.search))
    
    result = await tool.search(
        context=context,
        query="What is Amazon account health?"
    )

    print(result)


asyncio.run(main())