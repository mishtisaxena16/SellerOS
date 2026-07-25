"""
metadata.py

SellerOS Knowledge Engine

Responsibilities:
    - Metadata generation
    - Platform detection
    - Module detection
    - Capability extraction
    - Feature extraction
    - Workflow extraction
    - Tag generation
    - Keyword generation

Must NOT include:
    - Embeddings
    - ChromaDB
    - Retrieval
"""

from __future__ import annotations

import re

from pathlib import Path
from typing import Dict, List

from chunking import Chunk

from config import MODULE_MAPPING
from pprint import pprint
from chunking import ChunkingPipeline

# ==========================================================
# CONSTANTS
# ==========================================================

STOPWORDS = {
    "the", "a", "an", "and", "or", "but",
    "for", "with", "into", "from", "that",
    "this", "these", "those", "is", "are",
    "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "at", "by",
    "as", "it", "its", "their", "there",
    "will", "can", "may", "must", "should",
}

HIGH_PRIORITY_TERMS = {
    "must",
    "required",
    "mandatory",
    "critical",
    "important",
    "compliance",
    "guideline",
    "guidelines",
    "policy",
    "policies",
    "prohibited",
    "restriction",
    "restrictions",
    "not allowed",
    "warning",
}

ADVANCED_TERMS = {
    "optimization",
    "analytics",
    "advertising",
    "campaign",
    "forecast",
    "performance",
}

BEGINNER_TERMS = {
    "introduction",
    "getting started",
    "overview",
    "basic",
    "basics",
}


# ==========================================================
# METADATA GENERATOR
# ==========================================================

class MetadataGenerator:

    def __init__(self):
        self.module_mapping = MODULE_MAPPING

    # ======================================================
    # PUBLIC API
    # ======================================================

    def generate(
        self,
        chunk: Chunk,
        document_path: str | Path,
    ) -> Dict:

        document_path = Path(document_path)

        platform = self._detect_platform(
            document_path
        )

        module = self._detect_module(
            chunk.text,
            chunk.heading_path,
        )

        capability = self._extract_capability(
            chunk.heading_path
        )

        feature = self._extract_feature(
            chunk.heading_path
        )

        workflow = self._extract_workflow(
            chunk.heading_path
        )

        metadata = {

            "chunk_id": chunk.chunk_id,

            "platform": platform,

            "platform_scope": platform,

            "module": module,

            "capability": capability,

            "feature": feature,

            "workflow": workflow,

            "document": document_path.stem,

            "document_type": "knowledge",

            "source": str(document_path).replace(
                "\\",
                "/",
                ),

            "status": "active",

            "last_updated": "",

            "section": chunk.section,

            "heading_path": (
                chunk.heading_path
                if chunk.heading_path
                else["general"]
            ),

            "chunk_index": chunk.chunk_index,

            "total_chunks": chunk.total_chunks,

            "previous_chunk": chunk.previous_chunk,

            "next_chunk": chunk.next_chunk,

            "tags": self._generate_tags(
                platform,
                chunk,
                document_path,
            ),

            "keywords": (
                self._extract_keywords(chunk.text)
                or ["general"]
            ),

            "priority": self._detect_priority(
                chunk.text
            ),

            "seller_level": self._detect_seller_level(
                chunk.text
            ),

            "language": "en",

            "token_count": chunk.token_count,
        }
        validator = MetadataValidator()
        validator.validate(metadata)
        return metadata

    # ======================================================
    # PLATFORM DETECTION
    # ======================================================

    def _detect_platform(
        self,
        path: Path,
    ) -> str:

        path_lower = str(path).lower()

        platforms = [
            "amazon",
            "flipkart",
            "meesho",
            "gst",
            "sustainability",
        ]

        for platform in platforms:
            if platform in path_lower:
                return platform

        return "general"

    # ======================================================
    # MODULE DETECTION
    # ======================================================

    def _detect_module(
        self,
        text: str,
        heading_path: List[str],
    ) -> str:

        combined = (
            " ".join(heading_path)
            + " "
            + text[:1000]
        ).lower()

        for module, keywords in (
            self.module_mapping.items()
        ):
            for keyword in keywords:
                if keyword.lower() in combined:
                    return module

        return "general"

    # ======================================================
    # HIERARCHY EXTRACTION
    # ======================================================

    def _extract_capability(
        self,
        heading_path: List[str],
    ) -> str:
        
        if len(heading_path) >= 2:
            return self._slugify(
                heading_path[1]
            )
        
        if len(heading_path) >= 1:
            return self._slugify(
                heading_path[0]
            )
        
        

        return ""

    def _extract_feature(
        self,
        heading_path: List[str],
    ) -> str:

        if len(heading_path) >= 3:
            return self._slugify(
                heading_path[2]
            )

        return ""

    def _extract_workflow(
        self,
        heading_path: List[str],
    ) -> str:

        if len(heading_path) >= 4:
            return self._slugify(
                heading_path[3]
            )

        return ""

    # ======================================================
    # TAG GENERATION
    # ======================================================

    def _generate_tags(
        self,
        platform: str,
        chunk: Chunk,
        document_path: Path,
    ):
        tags = set()

        tags.add(platform.lower())

        tags.add(
            document_path.stem.lower()
        )

        tags.add(
            chunk.section.lower()
        )

        for heading in chunk.heading_path:
            tags.add(
                heading.lower()
            )

        cleaned_tags = []

        for tag in tags:

            tag = re.sub(
                r"[^a-z0-9_ ]",
                "",
                tag,
            )

            tag = tag.strip()

            if tag:
                cleaned_tags.append(tag)

        return sorted(cleaned_tags)

    # ======================================================
    # KEYWORD EXTRACTION
    # ======================================================

    def _extract_keywords(
        self,
        text: str,
        top_k: int = 15,
    ):
        words = re.findall(
            r"\b[a-zA-Z]{3,}\b",
            text.lower()
        )

        frequency = {}

        for word in words:

            if word in STOPWORDS:
                continue

            frequency[word] = (
                frequency.get(word, 0)
                + 1
            )

        ranked = sorted(
            frequency.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            word
            for word, _
            in ranked[:top_k]
        ]

    # ======================================================
    # PRIORITY DETECTION
    # ======================================================

    def _detect_priority(
        self,
        text: str,
    ) -> str:

        text = text.lower()
        
        high_matches = sum(
            1
            for term in HIGH_PRIORITY_TERMS
            if term in text
        )
        
        if high_matches >=2:
            return "high"
        
        if high_matches >=1:
            return "medium"
        
        return "low"

    # ======================================================
    # SELLER LEVEL DETECTION
    # ======================================================

    def _detect_seller_level(
        self,
        text: str,
    ) -> str:

        text = text.lower()

        if any(
            term in text
            for term in BEGINNER_TERMS
        ):
            return "beginner"

        if any(
            term in text
            for term in ADVANCED_TERMS
        ):
            return "advanced"

        return "intermediate"

    # ======================================================
    # UTILITIES
    # ======================================================

    @staticmethod
    def _slugify(
        text: str,
    ) -> str:

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9]+",
            "_",
            text,
        )

        return text.strip("_")

class MetadataValidator:

    REQUIRED_FIELDS = [
        "chunk_id",
        "platform",
        "module",
        "section",
        "heading_path",
        "token_count",
    ]

    def validate(
        self,
        metadata: Dict,
    ) -> bool:

        for field in self.REQUIRED_FIELDS:

            if field not in metadata:
                raise ValueError(
                    f"Missing metadata field: {field}"
                )

        if not metadata["chunk_id"]:
            raise ValueError(
                "chunk_id cannot be empty"
            )

        if metadata["token_count"] <= 0:
            raise ValueError(
                "token_count must be positive"
            )

        return True   
    
if __name__ == "__main__":


    document_path = (
        "SellerOS/knowledge/amazon/Listings.md"
    )

    pipeline = ChunkingPipeline()

    chunks = pipeline.process_document(
        document_path
    )

    generator = MetadataGenerator()

    metadata = generator.generate(
        chunks[0],
        document_path,
    )

    pprint(metadata)

    