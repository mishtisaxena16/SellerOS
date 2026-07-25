"""
exceptions.py

Exception hierarchy for the SellerOS Memory Layer.

Design rationale
-----------------
Earlier versions raised bare `ValueError` for "not found" conditions.
That is indistinguishable, from a caller's point of view, from a
programming error (e.g. passing the wrong type). Callers one layer up
(Agents, Orchestrator) need to be able to catch "memory not found" and
react gracefully (e.g. create a fresh seller profile) without
accidentally swallowing unrelated bugs.

All exceptions in this module derive from `MemoryError` so callers can
choose to catch broadly (`except MemoryError`) or narrowly
(`except MemoryNotFoundError`).
"""

from __future__ import annotations


class MemoryError(Exception):
    """Base class for every exception raised by the Memory Layer."""


class MemoryNotFoundError(MemoryError):
    """
    Raised when a requested memory object does not exist.

    Example
    -------
    ConversationManager.add_message("unknown_session", ...) raises this
    instead of a bare ValueError, so the Orchestrator can distinguish
    "no such session" from a malformed request.
    """


class InvalidMemoryOperationError(MemoryError):
    """
    Raised when an operation is requested that the Memory Layer cannot
    perform given the current state (e.g. merging two memory objects
    that belong to different sellers).
    """
