"""
models.py

Defines every memory object used by the SellerOS Memory Layer.

Memory Types
------------
1. ConversationMemory  - short-term, per-session chat history
2. SellerMemory        - slow-changing seller preferences
3. BusinessMemory      - long-term business facts and metrics

These models are storage-agnostic. Whether memory ends up in an
in-memory dict, Redis, or PostgreSQL, these shapes stay unchanged.

Design notes
------------
- Timestamps use `datetime.now(timezone.utc)` rather than the
  deprecated `datetime.utcnow()`. `utcnow()` returns a *naive*
  datetime, which silently breaks comparisons against timezone-aware
  values (e.g. rows read back from PostgreSQL's `timestamptz`
  columns) and is scheduled for removal in future CPython versions.
- `ChatMessage.message_id` was added so individual messages can be
  referenced (e.g. for edits, deletions, or citing "the message where
  the seller approved the price change") instead of only being
  addressable by position in a list.
- `Warehouse` is a nested Pydantic model, not a primitive. This
  matters for `updater.py`: Pydantic v2 models are unhashable by
  default (defining `__eq__` sets `__hash__ = None` unless the model
  is frozen), so any list-merge logic that relies on `dict.fromkeys`
  cannot be used on `list[Warehouse]` without a key-based merge. See
  `updater.py` for the fix.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def _new_id() -> str:
    """Generate a unique identifier for memory sub-objects."""
    return uuid.uuid4().hex


# ==========================================================
# Conversation Memory
# ==========================================================

class ChatMessage(BaseModel):
    """Represents a single message exchanged during a conversation."""

    message_id: str = Field(default_factory=_new_id)

    role: str  # "user" / "assistant" / "system"

    content: str

    timestamp: datetime = Field(default_factory=_utc_now)

    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationMemory(BaseModel):
    """
    Stores one complete conversation session.

    This is SHORT-TERM memory. Long conversations are expected to be
    summarized (see `summarizer.py`) rather than replayed in full to
    an LLM.
    """

    session_id: str

    seller_id: str

    marketplace: Optional[str] = None

    workflow: Optional[str] = None

    intent: Optional[str] = None

    messages: list[ChatMessage] = Field(default_factory=list)

    summary: Optional[str] = None

    tool_results: dict[str, Any] = Field(default_factory=dict)

    active_agent: Optional[str] = None

    approval_required: bool = False

    approval_granted: Optional[bool] = None

    total_tokens: int = 0

    created_at: datetime = Field(default_factory=_utc_now)

    updated_at: datetime = Field(default_factory=_utc_now)


# ==========================================================
# Seller Memory
# ==========================================================

class SellerMemory(BaseModel):
    """
    Personal preferences of the seller. Changes slowly over time.
    """

    seller_id: str

    seller_name: str

    email: Optional[str] = None

    phone: Optional[str] = None

    preferred_language: str = "English"

    preferred_currency: str = "INR"

    preferred_marketplace: Optional[str] = None

    connected_marketplaces: list[str] = Field(default_factory=list)

    preferred_llm: Optional[str] = None

    preferred_models: list[str] = Field(default_factory=list)

    notification_preferences: dict[str, bool] = Field(default_factory=dict)

    dashboard_preferences: dict[str, Any] = Field(default_factory=dict)

    settings: dict[str, Any] = Field(default_factory=dict)

    updated_at: datetime = Field(default_factory=_utc_now)


# ==========================================================
# Warehouse (nested inside Business Memory)
# ==========================================================

class Warehouse(BaseModel):
    """A single warehouse/fulfillment location owned by the seller."""

    warehouse_id: str

    name: str

    city: Optional[str] = None

    state: Optional[str] = None

    country: Optional[str] = None

    pin_code: Optional[str] = None


# ==========================================================
# Business Memory
# ==========================================================

class BusinessMemory(BaseModel):
    """
    Long-term business knowledge. Should survive across every
    conversation and change relatively infrequently.
    """

    seller_id: str

    business_name: str

    legal_business_name: Optional[str] = None

    gstin: Optional[str] = None

    pan: Optional[str] = None

    cin: Optional[str] = None

    business_type: Optional[str] = None

    business_category: Optional[str] = None

    year_established: Optional[int] = None

    marketplaces: list[str] = Field(default_factory=list)

    brands: list[str] = Field(default_factory=list)

    warehouses: list[Warehouse] = Field(default_factory=list)

    shipping_partners: list[str] = Field(default_factory=list)

    bank_account_verified: bool = False

    business_goals: list[str] = Field(default_factory=list)

    revenue_metrics: dict[str, Any] = Field(default_factory=dict)

    inventory_metrics: dict[str, Any] = Field(default_factory=dict)

    performance_metrics: dict[str, Any] = Field(default_factory=dict)

    advertising_metrics: dict[str, Any] = Field(default_factory=dict)

    sustainability_metrics: dict[str, Any] = Field(default_factory=dict)

    last_sync_time: Optional[datetime] = None

    updated_at: datetime = Field(default_factory=_utc_now)
