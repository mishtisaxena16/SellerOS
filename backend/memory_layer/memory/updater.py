"""
updater.py

SellerOS Memory Layer - intelligent merging of existing memory with
new incoming data, without losing useful information.

Rules
-----
- Never overwrite valid data with None.
- Merge lists (deduplicated).
- Merge dicts (shallow update).
- Replace primitive values.

Bug fix note
------------
The previous implementation deduplicated every list with
`list(dict.fromkeys(old + new))`. That relies on list elements being
hashable. It works for `list[str]` (brands, shipping_partners,
business_goals) but `BusinessMemory.warehouses` is `list[Warehouse]`,
and Pydantic v2 models are unhashable by default (defining `__eq__`
sets `__hash__ = None` unless the model is frozen). The first time two
updates both touched `warehouses`, this raised
`TypeError: unhashable type: 'Warehouse'`.

The fix below dedupes primitive lists the same way as before, but
dedupes lists of models by an identity key (e.g. `warehouse_id`),
keeping the newest value for any duplicate key rather than relying on
object identity/hashing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .models import BusinessMemory, ConversationMemory, SellerMemory

# Maps a field name to the attribute that uniquely identifies each
# element, for fields whose values are lists of models rather than
# lists of primitives. Add an entry here whenever a new list[Model]
# field is introduced.
_LIST_MERGE_KEYS: dict[str, str] = {
    "warehouses": "warehouse_id",
}


class MemoryUpdater:
    """Updates memory objects while preserving existing useful data."""

    # ----------------------------------------------------
    # Generic merge helpers
    # ----------------------------------------------------

    def _merge_model_list(self, old: list[Any], new: list[Any], key: str) -> list[Any]:
        """
        Merge two lists of Pydantic models, deduplicated by `key`.

        Later entries win on key collision (the incoming "new" value
        for warehouse X replaces the old one, rather than keeping a
        stale duplicate around).
        """
        merged: dict[Any, Any] = {}

        for item in old + new:
            identifier = getattr(item, key, None)
            merged[identifier] = item

        return list(merged.values())

    def _merge_value(self, old: Any, new: Any, field_name: str | None = None) -> Any:
        """
        Merge two field values.

        Rules
        -----
        new is None            -> keep old
        both are lists          -> merge (key-based if `field_name` is
                                    registered in `_LIST_MERGE_KEYS`,
                                    otherwise plain dedup for hashable
                                    primitives)
        both are dicts           -> shallow update, new wins
        anything else            -> replace with new
        """

        if new is None:
            return old

        if isinstance(old, list) and isinstance(new, list):
            merge_key = _LIST_MERGE_KEYS.get(field_name or "")

            if merge_key is not None:
                return self._merge_model_list(old, new, merge_key)

            if old and isinstance(old[0], BaseModel):
                # A list of models we don't have a registered merge
                # key for. Fail loudly rather than silently crashing
                # deep inside dict.fromkeys, and rather than silently
                # dropping data by picking one side.
                raise TypeError(
                    f"Cannot merge list field {field_name!r}: elements are "
                    f"{type(old[0]).__name__} models with no entry in "
                    f"_LIST_MERGE_KEYS. Add one specifying the identifying "
                    f"attribute (e.g. an '_id' field)."
                )

            return list(dict.fromkeys(old + new))

        if isinstance(old, dict) and isinstance(new, dict):
            merged = old.copy()
            merged.update(new)
            return merged

        return new

    # ----------------------------------------------------
    # Seller Memory
    # ----------------------------------------------------

    def update_seller_memory(self, existing: SellerMemory, new: SellerMemory) -> SellerMemory:
        """Merge `new` seller data into `existing`, preserving good values."""
        data = existing.model_dump()

        for field in data:
            data[field] = self._merge_value(data[field], getattr(new, field), field)

        return SellerMemory(**data)

    # ----------------------------------------------------
    # Business Memory
    # ----------------------------------------------------

    def update_business_memory(self, existing: BusinessMemory, new: BusinessMemory) -> BusinessMemory:
        """Merge `new` business data into `existing`, preserving good values."""
        data = existing.model_dump()

        for field in data:
            if field == "warehouses":
                # model_dump() turned Warehouse objects into plain
                # dicts; merge those dicts by warehouse_id, then let
                # BusinessMemory(**data) re-validate them back into
                # Warehouse models.
                data[field] = self._merge_dict_list(data[field], [w.model_dump() for w in new.warehouses], "warehouse_id")
                continue

            data[field] = self._merge_value(data[field], getattr(new, field), field)

        return BusinessMemory(**data)

    def _merge_dict_list(self, old: list[dict], new: list[dict], key: str) -> list[dict]:
        """Same idea as `_merge_model_list`, but operating on raw dicts
        (used after `model_dump()`, before re-validation)."""
        merged: dict[Any, dict] = {}
        for item in old + new:
            merged[item.get(key)] = item
        return list(merged.values())

    # ----------------------------------------------------
    # Conversation Memory
    # ----------------------------------------------------

    def update_conversation_memory(
        self,
        existing: ConversationMemory,
        new: ConversationMemory,
    ) -> ConversationMemory:
        """
        Merge `new` conversation data into `existing`.

        Messages are appended (not deduplicated - two genuinely
        identical messages sent at different times are both real
        events). The summary is replaced only if `new` provides one.
        Token counts are additive.
        """
        data = existing.model_dump()

        data["messages"] = existing.messages + new.messages

        if new.summary:
            data["summary"] = new.summary

        data["total_tokens"] = existing.total_tokens + new.total_tokens

        return ConversationMemory(**data)


# Singleton. Safe to share: this class holds no per-call state.
updater = MemoryUpdater()
