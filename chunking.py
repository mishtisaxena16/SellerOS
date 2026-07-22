"""
chunking.py

SellerOS Knowledge Engine

Responsibilities:
    - Document parsing
    - Heading tree construction
    - Section extraction
    - Semantic chunking
    - Adaptive chunking
    - Chunk relationships

Must NOT include:
    - Metadata generation
    - Embeddings
    - ChromaDB
    - Retrieval
"""

from __future__ import annotations

import re
import uuid
import hashlib
from cleaner import MarkdownCleaner
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from config import (
    TARGET_CHUNK_TOKENS,
    MAX_CHUNK_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    MIN_CHUNK_TOKENS,
)

# ==========================================================
# DATA MODELS
# ==========================================================

@dataclass
class Chunk:
    chunk_id: str
    text: str
    section: str
    heading_path: List[str]

    chunk_index: int = 0
    total_chunks: int = 0

    previous_chunk: Optional[str] = None
    next_chunk: Optional[str] = None

    @property
    def token_count(self) -> int:
        """
        SellerOS token estimation rule.
        """
        return len(self.text) // 4


@dataclass
class Section:
    title: str
    level: int
    heading_path: List[str]
    content: str


# ==========================================================
# MARKDOWN DOCUMENT PARSER
# ==========================================================

class MarkdownDocumentParser:
    """
    Reads markdown documents from disk.
    """

    def parse(self, file_path: str | Path) -> str:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        return path.read_text(
            encoding="utf-8",
            errors="ignore"
        )


# ==========================================================
# HEADING TREE BUILDER
# ==========================================================

class HeadingTreeBuilder:
    """
    Extract markdown headings and
    build heading hierarchy paths.
    """

    HEADING_PATTERN = re.compile(
        r"^(#{1,6})\s+(.*)$",
        re.MULTILINE
    )

    def extract_headings(
        self,
        markdown: str
    ):
        headings = []
        
        for match in self.HEADING_PATTERN.finditer(
            markdown
        ):
            title = match.group(2).strip()
            # Remove markdown bold formatting
            title = re.sub(
                r"\*\*(.*?)\*\*",
                r"\1",
                title,
            ).strip()
            
            headings.append(
                {
                    "level": len(match.group(1)),
                    "title": title,
                    "position": match.start(),
                }
            )

        return headings


# ==========================================================
# SECTION EXTRACTOR
# ==========================================================

class SectionExtractor:
    """
    Converts markdown content into sections.
    """

    def __init__(self):
        self.heading_builder = HeadingTreeBuilder()

    def extract_sections(
        self,
        markdown: str,
    ):
        headings = (
            self.heading_builder.extract_headings(
                markdown
            )
        )

        if not headings:
            return [
                Section(
                    title="Document",
                    level=0,
                    heading_path=[],
                    content=markdown.strip(),
                )
            ]

        sections: List[Section] = []

        path_stack: List[str] = []

        for index, heading in enumerate(headings):

            start_pos = heading["position"]

            if index + 1 < len(headings):
                end_pos = headings[index + 1]["position"]
            else:
                end_pos = len(markdown)

            raw_section = markdown[start_pos:end_pos]

            level = heading["level"]
            title = heading["title"]

            while len(path_stack) >= level:
                path_stack.pop()

            path_stack.append(title)

            content = self._remove_heading(
                raw_section
            )

            sections.append(
                Section(
                    title=title,
                    level=level,
                    heading_path=path_stack.copy(),
                    content=content.strip(),
                )
            )

        return sections

    @staticmethod
    def _remove_heading(text: str) -> str:

        lines = text.splitlines()

        if not lines:
            return text

        return "\n".join(lines[1:])


# ==========================================================
# SEMANTIC CHUNKER
# ==========================================================

class SemanticChunker:
    """
    Creates semantic blocks by splitting
    section content into paragraphs.
    """

    PARAGRAPH_PATTERN = re.compile(
        r"\n\s*\n"
    )

    def split_section(
        self,
        section: Section,
    ):
        content = section.content.strip()

        if not content:
            return []

        paragraphs = [
            p.strip()
            for p in self.PARAGRAPH_PATTERN.split(
                content
            )
            if p.strip()
        ]

        return paragraphs


# ==========================================================
# ADAPTIVE CHUNKER
# ==========================================================

class AdaptiveChunker:
    """
    Builds chunks from semantic blocks
    using adaptive sizing rules.
    """

    def __init__(self):
        self.target_tokens = TARGET_CHUNK_TOKENS
        self.max_tokens = MAX_CHUNK_TOKENS
        self.overlap_tokens = CHUNK_OVERLAP_TOKENS
        self.min_tokens = MIN_CHUNK_TOKENS

    @staticmethod
    def estimate_tokens(
        text: str
    ) -> int:
        return len(text) // 4

    def build_chunks(
        self,
        section: Section,
        semantic_blocks: List[str],
    ):
        chunks: List[Chunk] = []

        current_parts: List[str] = []
        current_tokens = 0

        for block in semantic_blocks:

            block_tokens = (
                self.estimate_tokens(block)
            )

            if block_tokens > self.max_tokens:

                if current_parts:

                    chunks.append(
                        self._create_chunk(
                            section,
                            "\n\n".join(
                                current_parts
                            ),
                        )
                    )

                    current_parts = []
                    current_tokens = 0

                chunks.extend(
                    self._split_large_block(
                        section,
                        block,
                    )
                )

                continue

            if (
                current_tokens + block_tokens
                > self.target_tokens
            ):

                if current_parts:

                    chunks.append(
                        self._create_chunk(
                            section,
                            "\n\n".join(
                                current_parts
                            ),
                        )
                    )

                current_parts = [block]
                current_tokens = block_tokens

            else:

                current_parts.append(block)
                current_tokens += block_tokens

        if current_parts:

            chunks.append(
                self._create_chunk(
                    section,
                    "\n\n".join(current_parts)
                )
            )

        return chunks

    def _split_large_block(
        self,
        section: Section,
        text: str,
    ):
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        chunks: List[Chunk] = []

        buffer: List[str] = []
        token_count = 0

        for sentence in sentences:

            sentence_tokens = (
                self.estimate_tokens(
                    sentence
                )
            )

            if (
                token_count + sentence_tokens
                > self.max_tokens
            ):

                if buffer:

                    chunks.append(
                        self._create_chunk(
                            section,
                            " ".join(buffer),
                        )
                    )

                buffer = [sentence]
                token_count = sentence_tokens

            else:

                buffer.append(sentence)
                token_count += sentence_tokens

        if buffer:

            chunks.append(
                self._create_chunk(
                    section,
                    " ".join(buffer),
                )
            )

        return chunks

    @staticmethod
    def _create_chunk(
        section: Section,
        text: str,
    ) -> Chunk:
        chunk_id= hashlib.md5(
            (
                section.title + "|" + text
            ).encode("utf-8")
        ).hexdigest()

        return Chunk(
            chunk_id= chunk_id,
            text=text.strip(),
            section=section.title,
            heading_path=section.heading_path.copy(),
        )


# ==========================================================
# CHUNK RELATIONSHIP BUILDER
# ==========================================================

class ChunkRelationshipBuilder:
    """
    Adds chunk relationships and indices.
    """

    def link_chunks(
        self,
        chunks: List[Chunk],
    ):
        total = len(chunks)

        for index, chunk in enumerate(
            chunks
        ):

            chunk.chunk_index = index
            chunk.total_chunks = total

            if index > 0:
                chunk.previous_chunk = (
                    chunks[
                        index - 1
                    ].chunk_id
                )

            if index < total - 1:
                chunk.next_chunk = (
                    chunks[
                        index + 1
                    ].chunk_id
                )

        return chunks


# ==========================================================
# CHUNKING PIPELINE
# ==========================================================

class ChunkingPipeline:

    def __init__(self):

        self.parser = (
            MarkdownDocumentParser()
        )
        
        self.cleaner = (
            MarkdownCleaner()
        )
        
        self.section_extractor = (
            SectionExtractor()
        )

        self.semantic_chunker = (
            SemanticChunker()
        )
        
        self.adaptive_chunker = (
            AdaptiveChunker()
        )

        self.relationship_builder = (
            ChunkRelationshipBuilder()
        )

    def process_document(
        self,
        file_path: str | Path,
    ):
        markdown = self.parser.parse(
            file_path
        )
        idx = markdown.find("There are two primary ways")
        
        markdown, report = self.cleaner.clean(
            markdown
        )
        
        sections = (
            self.section_extractor
            .extract_sections(markdown)
        )

        chunks: List[Chunk] = []

        for section in sections:

            semantic_blocks = (
                self.semantic_chunker
                .split_section(section)
            )

            section_chunks = (
                self.adaptive_chunker
                .build_chunks(
                    section,
                    semantic_blocks,
                )
            )

            chunks.extend(
                section_chunks
            )

        return (
            self.relationship_builder
            .link_chunks(chunks)
        )


# ==========================================================
# EXAMPLE USAGE
# ==========================================================

if __name__ == "__main__":

    pipeline = ChunkingPipeline()

    chunks = pipeline.process_document(
        "SellerOS/knowledge/amazon/Listings.md"
    )

    print(
        f"Generated {len(chunks)} chunks"
    )

    for chunk in chunks[:3]:

        print("=" * 80)
        print(
            f"ID: {chunk.chunk_id}"
        )
        print(
            f"Section: {chunk.section}"
        )
        print(
            f"Path: {chunk.heading_path}"
        )
        print(
            f"Tokens: {chunk.token_count}"
        )
        print(
            (chunk.text[:200])
        )
        