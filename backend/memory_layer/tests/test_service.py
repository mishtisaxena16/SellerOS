"""Tests for memory.service.MemoryService - the composed facade."""

from memory.models import BusinessMemory, SellerMemory, Warehouse
from memory.service import MemoryService


def test_get_agent_context_combines_seller_business_and_conversation(storage):
    service = MemoryService(storage)

    service.upsert_seller(SellerMemory(seller_id="s1", seller_name="ABC", preferred_marketplace="Amazon"))
    service.upsert_business(BusinessMemory(seller_id="s1", business_name="ABC", business_goals=["Grow"]))
    service.start_conversation("sess1", "s1")
    service.record_message("sess1", "user", "Create an optimized Amazon listing.")

    context = service.get_agent_context("s1", session_id="sess1")

    assert context["seller"]["marketplace"] == "Amazon"
    assert context["business"]["goals"] == ["Grow"]
    assert context["conversation_history"][0]["content"] == "Create an optimized Amazon listing."


def test_get_agent_context_without_session_omits_history(storage):
    service = MemoryService(storage)
    service.upsert_seller(SellerMemory(seller_id="s1", seller_name="ABC"))

    context = service.get_agent_context("s1")

    assert context["conversation_history"] == []


def test_upsert_seller_creates_then_merges(storage):
    service = MemoryService(storage)

    first = service.upsert_seller(
        SellerMemory(seller_id="s1", seller_name="ABC", connected_marketplaces=["Amazon"])
    )
    assert first.connected_marketplaces == ["Amazon"]

    second = service.upsert_seller(
        SellerMemory(seller_id="s1", seller_name="ABC", connected_marketplaces=["Flipkart"])
    )
    assert set(second.connected_marketplaces) == {"Amazon", "Flipkart"}


def test_upsert_business_merges_warehouses_without_crashing(storage):
    """
    End-to-end version of the warehouse-merge regression test, going
    through the public MemoryService API rather than calling
    MemoryUpdater directly.
    """
    service = MemoryService(storage)

    service.upsert_business(
        BusinessMemory(seller_id="s1", business_name="ABC", warehouses=[Warehouse(warehouse_id="wh_1", name="Delhi")])
    )
    merged = service.upsert_business(
        BusinessMemory(seller_id="s1", business_name="ABC", warehouses=[Warehouse(warehouse_id="wh_2", name="Mumbai")])
    )

    assert {w.warehouse_id for w in merged.warehouses} == {"wh_1", "wh_2"}


def test_persist_conversation_summary(storage):
    service = MemoryService(storage)
    service.start_conversation("sess1", "s1")
    service.record_message("sess1", "user", "Improve my Amazon title.")

    summary = service.persist_conversation_summary("sess1")

    assert "Improve my Amazon title." in summary
    stored = service.manager.get_conversation("sess1")
    assert stored.summary == summary


def test_search_conversation(storage):
    service = MemoryService(storage)
    service.start_conversation("sess1", "s1")
    service.record_message("sess1", "user", "How do I price my Amazon product?")
    service.record_message("sess1", "user", "What's the weather today?")

    results = service.search_conversation("sess1", "Amazon price")

    assert len(results) == 1
    assert "price" in results[0].content.lower()
