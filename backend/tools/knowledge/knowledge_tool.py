"""
KnowledgeTool — wraps the RAG layer (Retriever -> ChromaDB -> Context
Builder) described in the master change log.

Status: WIRED. This used to raise NOT_IMPLEMENTED because the RAG
layer lived in a different, earlier project (the Flask-based SellerOS
copilot) and hadn't been connected yet. It now imports the real
`Retriever` from that project (Marketsellers/SellerOS/retrieve.py) via
engine_bridge.py, which only adds that project's folder to sys.path —
retrieve.py, config.py, embedding.py, and chunking.py are untouched.

The call shape agents already use (`knowledge_tool.search(...)` / the
`execute(query=..., filters=..., top_k=...)` used by ContextBuilder and
SellerCoachAgent's default_plan) hasn't changed, so no agent needed
to change for this to start returning real results.

Runtime requirements (only matter when actually calling this tool,
not at import time):
- A local Ollama server running with the `qwen3-embedding:0.6b` model
  pulled (see SellerOS/config.py: EMBEDDING_MODEL / OLLAMA_HOST).
- A populated ChromaDB collection at SellerOS/data/chroma_db, built by
  SellerOS/ingest.py.
If either is missing, this fails loudly with a real error (connection
error, or a chromadb "collection not found" error) instead of quietly
returning an empty result — same "fail loudly" principle as the stub
this file replaces.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from tools.base.base_tool import BaseTool
from tools.base.tool_context import ToolContext
from tools.base.tool_result import ToolResult
from tools.knowledge.engine_bridge import ensure_on_path

# Must run before importing anything from the Knowledge Engine project.
ensure_on_path()

from retrieve import Retriever, RetrievedChunk  # noqa: E402 (see ensure_on_path() above)


def _chunk_to_dict(chunk: RetrievedChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "text": chunk.text,
        "metadata": chunk.metadata,
        "score": chunk.score,
    }


class KnowledgeTool(BaseTool):
    name = "knowledge_tool"
    description = (
        "Searches the SellerOS knowledge base (marketplace policies, GST, "
        "sustainability docs) for content relevant to a query. Backed by "
        "the real ChromaDB Retriever."
    )
    permissions: list[str] = ["knowledge:read"]

    def __init__(self) -> None:
        # One Retriever per KnowledgeTool instance, built lazily on first
        # use rather than in __init__: tool_registry.build_default_registry()
        # constructs every tool eagerly at app startup, and Retriever.__init__
        # opens a persistent Chroma client immediately. Building it lazily
        # means a missing/unbuilt ChromaDB collection doesn't crash app
        # startup for every other tool — it only fails the first time
        # something actually asks the knowledge base a question.
        self._retriever: Optional[Retriever] = None

    def _get_retriever(self) -> Retriever:
        if self._retriever is None:
            self._retriever = Retriever()
        return self._retriever

    async def execute(
        self,
        context: ToolContext,
        query: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 5,
        include_neighbors: bool = True,
        **kwargs: Any,
    ) -> ToolResult:
        if not query:
            return ToolResult.fail(
                message="knowledge_tool.search requires a non-empty 'query'.",
                error="VALIDATION_ERROR",
            )

        retriever = self._get_retriever()
        platform = (filters or {}).get("platform")
        module = (filters or {}).get("module")

        def _run_search() -> list[RetrievedChunk]:
            if platform:
                return retriever.search_platform(query=query, platform=platform, top_k=top_k)
            if module:
                return retriever.search_module(query=query, module=module, top_k=top_k)
            return retriever.search(query=query, top_k=top_k)

        # Retriever's methods are synchronous, blocking calls (HTTP to
        # Ollama for the query embedding, then a ChromaDB query) — run
        # them off the event loop so one slow knowledge lookup doesn't
        # stall every other concurrent agent/tool call.
        chunks = await asyncio.to_thread(_run_search)

        if include_neighbors and chunks:
            chunks = await asyncio.to_thread(retriever.expand_neighbors, chunks)

        if not chunks:
            return ToolResult.ok(
                data="",
                message=f"No knowledge base results found for query: {query!r}.",
                metadata={"chunks": [], "query": query},
            )

        context_text = await asyncio.to_thread(retriever.build_context, chunks)

        return ToolResult.ok(
            data=context_text,
            message=f"Retrieved {len(chunks)} chunk(s) from the knowledge base.",
            metadata={"chunks": [_chunk_to_dict(c) for c in chunks], "query": query},
        )

    async def search(
        self,
        context: ToolContext,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 5,
    ) -> ToolResult:
        """Convenience alias matching the spec's `knowledge_tool.search(...)` call shape."""
        return await self.run(context, query=query, filters=filters, top_k=top_k)
