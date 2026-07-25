"""
ingest.py

SellerOS Knowledge Engine

Responsibilities:
    - Discover markdown documents
    - Generate chunks
    - Generate metadata
    - Generate embeddings
    - Store vectors in ChromaDB

Pipeline:

Markdown
    ↓
Chunking
    ↓
Metadata
    ↓
Embedding
    ↓
ChromaDB
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import chromadb

from chunking import ChunkingPipeline
from metadata import MetadataGenerator
from embedding import EmbeddingGenerator

from config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_PATH,
    KNOWLEDGE_DIRECTORIES,
)
IGNORED_FILES = {
    "readme.md",
}

# ==========================================================
# INGESTION PIPELINE
# ==========================================================

class IngestionPipeline:

    def __init__(self) -> None:

        self.chunker = ChunkingPipeline()

        self.metadata_generator = (
            MetadataGenerator()
        )

        self.embedding_generator = (
            EmbeddingGenerator()
        )

        self.client = (
            chromadb.PersistentClient(
                path=str(CHROMA_DB_PATH)
            )
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME
            )
        )

    # ======================================================
    # INGEST SINGLE DOCUMENT
    # ======================================================

    def ingest_document(
        self,
        document_path: str | Path,
    ) -> int:

        document_path = Path(document_path)

        print(
            f"\nProcessing: {document_path}"
        )

        chunks = (
            self.chunker.process_document(
                document_path
            )
        )

        inserted_count = 0

        for chunk in chunks:

            metadata = (
                self.metadata_generator.generate(
                    chunk,
                    document_path,
                )
            )

            embedded_chunk = (
                self.embedding_generator
                .generate_chunk_embedding(
                    chunk,
                    metadata,
                )
            )

            self.collection.upsert(
                ids=[
                    embedded_chunk.chunk_id
                ],
                documents=[
                    embedded_chunk.text
                ],
                embeddings=[
                    embedded_chunk.embedding
                ],
                metadatas=[
                    embedded_chunk.metadata
                ],
            )

            inserted_count += 1

        print(
            f"Inserted {inserted_count} chunks"
        )

        return inserted_count

    # ======================================================
    # INGEST ALL KNOWLEDGE SOURCES
    # ======================================================

    def ingest_all(self) -> int:

        total_chunks = 0

        for (
            platform,
            directory
        ) in KNOWLEDGE_DIRECTORIES.items():

            if not directory.exists():

                print(
                    f"Skipping missing directory: "
                    f"{directory}"
                )

                continue

            print(
                f"\n{'=' * 80}"
            )
            print(
                f"Ingesting Platform: "
                f"{platform.upper()}"
            )
            print(
                f"{'=' * 80}"
            )

            markdown_files = list(
                directory.rglob("*.md")
            )

            print(
                f"Found "
                f"{len(markdown_files)} "
                f"documents"
            )

            for file_path in markdown_files:
                if(
                    file_path.name.lower()
                    in IGNORED_FILES
                ):
                    continue
                try:
                    
                    total_chunks += (
                        self.ingest_document(
                            file_path
                        )
                    )
                except FileNotFoundError:
                    print(f"Skipping missing file: {file_path}")
                except Exception as e:
                    print(
                        f"Failed to ingest: "
                        f"{file_path}" 
                    )
                    print(f"Reason: {e}")
                    

        return total_chunks

    # ======================================================
    # COLLECTION HELPERS
    # ======================================================

    def collection_count(self) -> int:

        return self.collection.count()

    def peek(self, limit: int = 1):

        return self.collection.peek(
            limit=limit
        )

    def reset_collection(self) -> None:

        try:

            self.client.delete_collection(
                CHROMA_COLLECTION_NAME
            )

        except Exception:
            pass

        self.collection = (
            self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME
            )
        )

        print(
            "Collection reset completed."
        )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    pipeline = IngestionPipeline()

    total_chunks = (
        pipeline.ingest_all()
    )

    print("\n")
    print("=" * 80)
    print("INGESTION COMPLETE")
    print("=" * 80)

    print(
        f"Total Chunks Added: "
        f"{total_chunks}"
    )

    print(
        f"Collection Count: "
        f"{pipeline.collection_count()}"
    )

    sample = pipeline.peek(1)

    print("\nSample Record:")
    print(sample)