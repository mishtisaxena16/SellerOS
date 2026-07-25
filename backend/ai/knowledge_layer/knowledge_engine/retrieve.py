"""
retrieve.py

SellerOS Knowledge Engine

Responsibilities:
    - Query embedding generation
    - ChromaDB vector search
    - Metadata filtering
    - Neighbor expansion
    - Context assembly

Must NOT:
    - Generate answers
    - Call LLMs
    - Route agents
    - Build prompts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import chromadb

from config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_PATH,
)

from embedding import EmbeddingGenerator


# ==========================================================
# DATA MODEL
# ==========================================================

@dataclass
class RetrievedChunk:

    chunk_id: str

    text: str

    metadata: Dict[str, Any]

    score: float


# ==========================================================
# RETRIEVER
# ==========================================================

class Retriever:

    def __init__(self) -> None:

        self.embedding_generator = (
            EmbeddingGenerator()
        )

        self.client = (
            chromadb.PersistentClient(
                path=str(CHROMA_DB_PATH)
            )
        )

        self.collection = (
            self.client.get_collection(
                name=CHROMA_COLLECTION_NAME
            )
        )

    # ======================================================
    # SEARCH
    # ======================================================

    def search(
        self,
        query: str,
        top_k: int = 5,
    ):
        query_embedding = (
            self.embedding_generator
            .generate_embedding(query)
        )

        results = self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=top_k,
        )

        return self._convert_results(
            results
        )

    # ======================================================
    # PLATFORM FILTER SEARCH
    # ======================================================

    def search_platform(
        self,
        query: str,
        platform: str,
        top_k: int = 5,
    ):
        query_embedding = (
            self.embedding_generator
            .generate_embedding(query)
        )

        results = self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=top_k,
            where={
                "platform": platform
            },
        )

        return self._convert_results(
            results
        )

    # ======================================================
    # MODULE FILTER SEARCH
    # ======================================================

    def search_module(
        self,
        query: str,
        module: str,
        top_k: int = 5,
    ):
        query_embedding = (
            self.embedding_generator
            .generate_embedding(query)
        )

        results = self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=top_k,
            where={
                "module": module
            },
        )

        return self._convert_results(
            results
        )

    # ======================================================
    # NEIGHBOR EXPANSION
    # ======================================================

    def expand_neighbors(
        self,
        chunks: List[RetrievedChunk],
    ): 
        expanded: Dict[
            str,
            RetrievedChunk
        ] = {}

        for chunk in chunks:

            expanded[
                chunk.chunk_id
            ] = chunk

            previous_id = (
                chunk.metadata.get(
                    "previous_chunk"
                )
            )

            next_id = (
                chunk.metadata.get(
                    "next_chunk"
                )
            )

            for neighbor_id in (
                previous_id,
                next_id,
            ):

                if not neighbor_id:
                    continue

                if neighbor_id in expanded:
                    continue

                neighbor = (
                    self.fetch_chunk_by_id(
                        neighbor_id
                    )
                )

                if neighbor:

                    expanded[
                        neighbor.chunk_id
                    ] = neighbor

        return list(
            expanded.values()
        )

    # ======================================================
    # FETCH CHUNK BY ID
    # ======================================================

    def fetch_chunk_by_id(
        self,
        chunk_id: str,
    ):
        result = self.collection.get(
            ids=[chunk_id]
        )

        if not result["ids"]:
            return None

        return RetrievedChunk(
            chunk_id=result["ids"][0],
            text=result["documents"][0],
            metadata=result["metadatas"][0],
            score=0.0,
        )

    # ======================================================
    # CONTEXT BUILDER
    # ======================================================

    def build_context(
        self,
        chunks: List[RetrievedChunk],
    ) -> str:

        context_parts = []

        for chunk in chunks:

            section = (
                chunk.metadata.get(
                    "section",
                    ""
                )
            )

            context_parts.append(
                f"[SECTION]\n"
                f"{section}\n\n"
                f"{chunk.text}"
            )

        return (
            "\n\n"
            + "=" * 80
            + "\n\n"
        ).join(
            context_parts
        )

    # ======================================================
    # FULL RETRIEVAL
    # ======================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        include_neighbors: bool = True,
    ) -> str:

        chunks = self.search(
            query=query,
            top_k=top_k,
        )

        if include_neighbors:

            chunks = (
                self.expand_neighbors(
                    chunks
                )
            )

        return self.build_context(
            chunks
        )

    # ======================================================
    # CHROMA RESULT CONVERSION
    # ======================================================

    def _convert_results(
        self,
        results: Dict[str, Any],
    ):
        output: List[
            RetrievedChunk
        ] = []

        ids = results.get(
            "ids",
            [[]]
        )[0]

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        for idx in range(
            len(ids)
        ):

            distance = 0.0

            if idx < len(distances):
                distance = float(
                    distances[idx]
                )

            output.append(

                RetrievedChunk(
                    chunk_id=ids[idx],
                    text=documents[idx],
                    metadata=metadatas[idx],
                    score=distance,
                )

            )

        return output


# ==========================================================
# TESTING
# ==========================================================

if __name__ == "__main__":

    retriever = Retriever()

    query = (
        "Meesho image guidelines"
    )

    results = retriever.search(
        query=query,
        top_k=3,
    )

    print(
        f"\nRetrieved "
        f"{len(results)} chunks\n"
    )

    for result in results:

        print("=" * 80)

        print(
            "Section:",
            result.metadata.get(
                "section"
            )
        )

        print(
            "Score:",
            result.score
        )

        print()

        print(
            result.text[:300]
        )

    print("\n")
    print("=" * 80)
    print("CONTEXT")
    print("=" * 80)

    context = retriever.retrieve(
        query=query,
        top_k=3,
        include_neighbors=True,
    )

    print(
        context[:1500]
    )