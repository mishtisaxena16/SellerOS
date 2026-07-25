"""
SellerOS Knowledge Engine Configuration

This module contains all global configuration, constants, paths,
schema definitions, retrieval settings, embedding settings,
and logging configuration used throughout the Knowledge Engine.

Author: SellerOS
Version: 1.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Final


# ============================================================================
# PROJECT PATHS
# ============================================================================
# This file's location, and the location of the knowledge docs / chroma
# data it points at, have moved more than once (most recently: the
# whole backend got reorganized under ai/*_layer/). Rather than encode
# today's exact relative depth as a fixed number of ".parent" calls —
# correct once, silently wrong the next time something moves — the two
# helpers below locate things by what they actually contain.
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent


def _find_knowledge_docs_dir() -> Path:
    # Current layout: knowledge_engine/ (this file) and knowledge_docs/
    # are siblings under knowledge_layer/. Check that first; fall back
    # to a bounded search so a future reorg doesn't silently break this
    # (an empty/missing KNOWLEDGE_DIR would make every ingest.py run
    # silently index nothing, which is a much worse failure mode than
    # a loud FileNotFoundError here).
    sibling = ROOT_DIR.parent / "knowledge_docs"
    if sibling.exists():
        return sibling
    for ancestor in list(ROOT_DIR.parents)[:6]:
        for candidate in ancestor.glob("**/knowledge_docs"):
            if candidate.is_dir():
                return candidate
    raise FileNotFoundError(
        "Could not locate the knowledge_docs/ directory (amazon/flipkart/"
        "meesho/gst/sustainability markdown sources) near config.py."
    )


def _find_chroma_data_dir() -> Path:
    # Current layout: SellerOS/chroma_data/ — several levels above this
    # file (knowledge_engine -> knowledge_layer -> ai -> backend ->
    # SellerOS). Search upward for it by name instead of hardcoding
    # that depth, for the same reason as above.
    for ancestor in ROOT_DIR.parents:
        candidate = ancestor / "chroma_data"
        if candidate.exists():
            return candidate
    # Not found anywhere above — this is a fresh checkout that hasn't
    # been ingested yet, not necessarily an error. Default to a
    # sensible location next to this file; ingest.py will create it.
    return ROOT_DIR / "chroma_data"


KNOWLEDGE_DIR: Final[Path] = _find_knowledge_docs_dir()

AMAZON_PATH: Final[Path] = KNOWLEDGE_DIR / "amazon"
FLIPKART_PATH: Final[Path] = KNOWLEDGE_DIR / "flipkart"
MEESHO_PATH: Final[Path] = KNOWLEDGE_DIR / "meesho"
GST_PATH: Final[Path] = KNOWLEDGE_DIR / "gst"
SUSTAINABILITY_PATH: Final[Path] = KNOWLEDGE_DIR / "sustainability"


KNOWLEDGE_DIRECTORIES: Final[Dict[str, Path]] = {
    "amazon": AMAZON_PATH,
    "flipkart": FLIPKART_PATH,
    "meesho": MEESHO_PATH,
    "gst": GST_PATH,
    "sustainability": SUSTAINABILITY_PATH,
}

DATA_DIR: Final[Path] = _find_chroma_data_dir()
CHROMA_DB_PATH: Final[Path] = DATA_DIR / "chroma_db"

LOG_DIR: Final[Path] = ROOT_DIR / "logs"


# ============================================================================
# DOCUMENT SETTINGS
# ============================================================================

SUPPORTED_FILE_EXTENSIONS: Final[tuple[str, ...]] = (
    ".md",
    ".markdown",
)

DEFAULT_LANGUAGE: Final[str] = "en"


# ==========================================================
# CHUNKING SETTINGS
# ==========================================================

TARGET_CHUNK_TOKENS = 500

MAX_CHUNK_TOKENS = 800

CHUNK_OVERLAP_TOKENS = 100

MIN_CHUNK_TOKENS = 50


# ============================================================================
# EMBEDDING SETTINGS
# ============================================================================

EMBEDDING_MODEL: Final[str] = (
    "nomic-embed-text"
)
OLLAMA_HOST = "http://localhost:11434"
EMBEDDING_BATCH_SIZE: Final[int] = 32

EMBEDDING_DEVICE: Final[str] = "cpu"
NORMALIZE_EMBEDDINGS: Final[bool] = True


# ============================================================================
# VECTOR DATABASE SETTINGS
# ============================================================================

CHROMA_COLLECTION_NAME: Final[str] = "selleros_knowledge"
CHROMA_DISTANCE_FUNCTION = "cosine"
PERSIST_VECTOR_DB: Final[bool] = True


# ============================================================================
# RETRIEVAL SETTINGS
# ============================================================================

VECTOR_SEARCH_TOP_K: Final[int] = 20

RERANK_TOP_K: Final[int] = 5

CONTEXT_NEIGHBOR_WINDOW: Final[int] = 1

ENABLE_RERANKING: Final[bool] = True


# ============================================================================
# RERANKER SETTINGS
# ============================================================================

RERANKER_MODEL: Final[str] = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


# ============================================================================
# SUPPORTED PLATFORMS
# ============================================================================

SUPPORTED_PLATFORMS: Final[tuple[str, ...]] = (
    "amazon",
    "flipkart",
    "meesho",
)

# ============================================================================
# MODULE MAPPING (FROZEN)
# ============================================================================

MODULE_MAPPING: Final[Dict[str, list[str]]] = {
    "product_studio": [
        "listing",
        "pricing",
        "catalog",
    ],
    "operations": [
        "inventory",
        "orders",
        "shipping",
        "returns",
    ],
    "marketing": [
        "ads",
        "promotions",
        "campaigns",
    ],
    "business_intelligence": [
        "analytics",
        "forecasting",
        "kpis",
    ],
    "seller_coach": [
        "registration",
        "policies",
        "gst",
        "learning",
    ],
    "sustainability": [
        "sustainability",
        "packaging",
        "compliance",
    ],
}