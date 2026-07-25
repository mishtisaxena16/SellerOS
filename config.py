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
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent
KNOWLEDGE_DIR: Final[Path] = ROOT_DIR / "knowledge"

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

DATA_DIR: Final[Path] = ROOT_DIR / "data"
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