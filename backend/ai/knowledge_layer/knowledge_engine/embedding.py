"""
embedding.py

SellerOS Knowledge Engine

Responsibilities:
    - Generate embeddings
    - Batch embedding generation
    - Embedding validation

Must NOT include:
    - ChromaDB
    - Retrieval
    - Reranking
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ollama import Client

from chunking import Chunk
from config import (
    EMBEDDING_MODEL,
    OLLAMA_HOST,
)


# ==========================================================
# DATA MODEL
# ==========================================================

@dataclass
class EmbeddedChunk:

    chunk_id: str

    text: str

    metadata: Dict

    embedding: List[float]


# ==========================================================
# EMBEDDING GENERATOR
# ==========================================================

class EmbeddingGenerator:

    def __init__(self):

        self.client = Client(
            host=OLLAMA_HOST
        )

    def generate_embedding(
        self,
        text: str,
    ):
        response = self.client.embeddings(
            model=EMBEDDING_MODEL,
            prompt=text,
        )

        embedding = response["embedding"]

        self._validate_embedding(
            embedding
        )

        return embedding

    def generate_chunk_embedding(
        self,
        chunk: Chunk,
        metadata: Dict,
    ) -> EmbeddedChunk:

        embedding = (
            self.generate_embedding(
                chunk.text
            )
        )

        return EmbeddedChunk(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            metadata=metadata,
            embedding=embedding,
        )

    def generate_batch_embeddings(
        self,
        chunks: List[Chunk],
        metadata_list: List[Dict],
    ):
        results = []

        for chunk, metadata in zip(
            chunks,
            metadata_list,
        ):

            results.append(
                self.generate_chunk_embedding(
                    chunk,
                    metadata,
                )
            )

        return results

    @staticmethod
    def _validate_embedding(
        embedding: List[float],
    ) -> None:

        if not isinstance(
            embedding,
            list,
        ):
            raise ValueError(
                "Embedding must be a list."
            )

        if len(embedding) == 0:
            raise ValueError(
                "Embedding cannot be empty."
            )