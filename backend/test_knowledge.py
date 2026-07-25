# test_knowledge.py

import asyncio
import inspect

from tools.knowledge.knowledge_tool import KnowledgeTool
from tools.base.tool_context import ToolContext


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