"""Tests for memory.updater.MemoryUpdater."""

import pytest

from memory.models import BusinessMemory, ConversationMemory, SellerMemory, Warehouse
from memory.updater import MemoryUpdater


def test_update_seller_memory_merges_lists_and_replaces_primitives():
    updater = MemoryUpdater()

    old = SellerMemory(
        seller_id="s1",
        seller_name="ABC Traders",
        preferred_language="English",
        connected_marketplaces=["Amazon"],
        settings={"theme": "dark"},
    )
    new = SellerMemory(
        seller_id="s1",
        seller_name="ABC Traders",
        preferred_language="Hindi",
        connected_marketplaces=["Flipkart"],
        settings={"notifications": True},
    )

    merged = updater.update_seller_memory(old, new)

    assert merged.preferred_language == "Hindi"  # primitive: replaced
    assert set(merged.connected_marketplaces) == {"Amazon", "Flipkart"}  # list: merged
    assert merged.settings == {"theme": "dark", "notifications": True}  # dict: merged


def test_update_seller_memory_never_overwrites_with_none():
    updater = MemoryUpdater()

    old = SellerMemory(seller_id="s1", seller_name="ABC Traders", email="old@example.com")
    new = SellerMemory(seller_id="s1", seller_name="ABC Traders", email=None)

    merged = updater.update_seller_memory(old, new)

    assert merged.email == "old@example.com"


def test_update_business_memory_merges_warehouses_without_crashing():
    """
    Regression test for the critical bug: merging BusinessMemory
    objects that both set `warehouses` used to raise
    `TypeError: unhashable type: 'Warehouse'` because the old
    implementation deduplicated every list with `dict.fromkeys`, which
    requires hashable elements. Pydantic v2 models are unhashable by
    default. This must now merge cleanly by `warehouse_id`.
    """
    updater = MemoryUpdater()

    old = BusinessMemory(
        seller_id="s1",
        business_name="ABC Traders",
        warehouses=[Warehouse(warehouse_id="wh_1", name="Delhi Hub")],
    )
    new = BusinessMemory(
        seller_id="s1",
        business_name="ABC Traders",
        warehouses=[Warehouse(warehouse_id="wh_2", name="Mumbai Hub")],
    )

    merged = updater.update_business_memory(old, new)  # must not raise

    warehouse_ids = {w.warehouse_id for w in merged.warehouses}
    assert warehouse_ids == {"wh_1", "wh_2"}


def test_update_business_memory_warehouse_merge_prefers_newer_on_id_collision():
    updater = MemoryUpdater()

    old = BusinessMemory(
        seller_id="s1",
        business_name="ABC Traders",
        warehouses=[Warehouse(warehouse_id="wh_1", name="Old Name", city="Delhi")],
    )
    new = BusinessMemory(
        seller_id="s1",
        business_name="ABC Traders",
        warehouses=[Warehouse(warehouse_id="wh_1", name="Updated Name", city="Delhi")],
    )

    merged = updater.update_business_memory(old, new)

    assert len(merged.warehouses) == 1
    assert merged.warehouses[0].name == "Updated Name"


def test_update_conversation_memory_appends_messages_and_sums_tokens():
    updater = MemoryUpdater()

    old = ConversationMemory(session_id="c1", seller_id="s1", total_tokens=100)
    new = ConversationMemory(session_id="c1", seller_id="s1", total_tokens=50)

    merged = updater.update_conversation_memory(old, new)

    assert merged.total_tokens == 150


def test_merge_value_raises_clearly_for_unregistered_model_lists():
    """
    If a future field introduces list[SomeNewModel] without registering
    a merge key, the updater should fail loudly and explain what to do,
    rather than crashing deep inside dict.fromkeys or silently dropping
    data.
    """
    updater = MemoryUpdater()

    class Unregistered:
        pass

    with pytest.raises(TypeError, match="_LIST_MERGE_KEYS"):
        updater._merge_value([Warehouse(warehouse_id="wh_1", name="A")], [Warehouse(warehouse_id="wh_2", name="B")], "unregistered_field")
