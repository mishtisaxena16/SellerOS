"""
sqlite_storage.py

Persistent storage backend for the SellerOS Memory Layer — resolves
the "conversation persistence" decision flagged as open in the
Backend Handoff doc, in favor of option (b): a real BaseMemoryStore
implementation living inside memory_layer/, swapped in for
InMemoryStorage, rather than a second, independent conversations
table built in the Application Backend. One source of truth for
conversation state, consistent with how every other storage-agnostic
seam in this project (Mock -> Live connectors, session_store's
register() seam) is meant to be swapped: the interface doesn't change,
only what's behind it.

Why sqlite3 (stdlib) and not SQLAlchemy
----------------------------------------
memory/base.py's own docstring states this layer "must be
independently importable from anywhere in the system" and uses
relative imports specifically to avoid depending on where the package
is mounted. Importing the Application Backend's SQLAlchemy `Base` /
`engine` here would quietly violate that — this layer would then only
import cleanly if the backend's database module happens to be
importable too. Plain `sqlite3` (stdlib, zero extra dependency) keeps
memory_layer's independence real rather than aspirational. It writes
to a *different* SQLite file than the backend's own `selleros.db` by
default — see DEFAULT_DB_PATH — deliberately: this store's job is
conversation/seller/business memory for the AI runtime, not sharing a
schema with the backend's users/sellers/marketplace_accounts tables.

Why JSON blobs and not a normalized relational schema
------------------------------------------------------
ConversationMemory / SellerMemory / BusinessMemory are already
storage-agnostic Pydantic models (see models.py). Storing each as one
JSON blob keyed by its ID is a correct, working persistence layer
today, and it's what "decide and implement conversation persistence"
in the handoff doc asked for — an honest, functioning store, not a
fully normalized schema with per-field indexes and migrations that
nothing currently needs. If a real query need shows up later (e.g.
"find every conversation where intent=pricing across all sellers"),
that's a concrete reason to add a normalized table for that one
access pattern — not a reason to hold up shipping a working store now.

Concurrency
-----------
sqlite3 with `check_same_thread=False` and a per-call connection
(rather than one long-lived connection reused across threads) is
adequate for a single backend process. If SellerOS moves to multiple
worker processes later, this is the seam to swap to Postgres — same
interface, this file's replacement, nothing above it changes.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .base import BaseMemoryStore
from .models import (
    BusinessMemory,
    ChatMessage,
    ConversationMemory,
    SellerMemory,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "memory_store.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS businesses (
    seller_id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
"""


class SQLiteMemoryStore(BaseMemoryStore):
    """Persistent BaseMemoryStore backend using stdlib sqlite3 + JSON blobs."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self._db_path = str(db_path)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    # ======================================================
    # Conversation Memory
    # ======================================================

    def save_conversation(self, conversation: ConversationMemory) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO conversations (session_id, data) VALUES (?, ?)",
                (conversation.session_id, conversation.model_dump_json()),
            )

    def load_conversation(self, session_id: str) -> ConversationMemory | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM conversations WHERE session_id = ?", (session_id,)
            ).fetchone()
        return ConversationMemory.model_validate_json(row[0]) if row else None

    def update_conversation(self, conversation: ConversationMemory) -> None:
        self.save_conversation(conversation)

    def delete_conversation(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))

    def load_messages(
        self,
        session_id: str,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        conversation = self.load_conversation(session_id)
        if conversation is None:
            return []
        messages = conversation.messages[offset:]
        if limit is not None:
            messages = messages[:limit]
        return messages

    # ======================================================
    # Seller Memory
    # ======================================================

    def save_seller(self, seller: SellerMemory) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sellers (seller_id, data) VALUES (?, ?)",
                (seller.seller_id, seller.model_dump_json()),
            )

    def load_seller(self, seller_id: str) -> SellerMemory | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM sellers WHERE seller_id = ?", (seller_id,)
            ).fetchone()
        return SellerMemory.model_validate_json(row[0]) if row else None

    def update_seller(self, seller: SellerMemory) -> None:
        self.save_seller(seller)

    def delete_seller(self, seller_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sellers WHERE seller_id = ?", (seller_id,))

    # ======================================================
    # Business Memory
    # ======================================================

    def save_business(self, business: BusinessMemory) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO businesses (seller_id, data) VALUES (?, ?)",
                (business.seller_id, business.model_dump_json()),
            )

    def load_business(self, seller_id: str) -> BusinessMemory | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM businesses WHERE seller_id = ?", (seller_id,)
            ).fetchone()
        return BusinessMemory.model_validate_json(row[0]) if row else None

    def update_business(self, business: BusinessMemory) -> None:
        self.save_business(business)

    def delete_business(self, seller_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM businesses WHERE seller_id = ?", (seller_id,))
