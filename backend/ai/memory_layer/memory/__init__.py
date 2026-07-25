"""
SellerOS Memory Layer.

Public API
----------
Callers outside this package should generally only need:

    from memory import MemoryService, InMemoryStorage
    from memory.models import SellerMemory, BusinessMemory, ConversationMemory, ChatMessage

    storage = InMemoryStorage()
    memory = MemoryService(storage)

Everything else (`MemoryManager`, `ConversationManager`,
`MemoryRetriever`, individual filter/search/summarizer/updater
classes) remains importable directly from its module for testing or
advanced use, but `MemoryService` is the intended entry point so that
internal composition can evolve without breaking callers.
"""

from .base import BaseMemoryStore
from .exceptions import InvalidMemoryOperationError, MemoryError, MemoryNotFoundError
from .models import BusinessMemory, ChatMessage, ConversationMemory, SellerMemory, Warehouse
from .service import MemoryService
from .storage import InMemoryStorage

__all__ = [
    "MemoryService",
    "BaseMemoryStore",
    "InMemoryStorage",
    "SellerMemory",
    "BusinessMemory",
    "ConversationMemory",
    "ChatMessage",
    "Warehouse",
    "MemoryError",
    "MemoryNotFoundError",
    "InvalidMemoryOperationError",
]
