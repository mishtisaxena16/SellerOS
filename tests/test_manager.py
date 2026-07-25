"""Tests for memory.manager.MemoryManager."""

import pytest

from memory.exceptions import MemoryNotFoundError
from memory.manager import MemoryManager
from memory.models import SellerMemory


def test_save_and_get_seller(storage):
    manager = MemoryManager(storage)
    seller = SellerMemory(seller_id="s1", seller_name="ABC Traders")

    manager.save_seller(seller)

    assert manager.get_seller("s1").seller_name == "ABC Traders"


def test_get_seller_returns_none_when_missing(storage):
    manager = MemoryManager(storage)
    assert manager.get_seller("nope") is None


def test_require_seller_raises_memory_not_found(storage):
    manager = MemoryManager(storage)
    with pytest.raises(MemoryNotFoundError):
        manager.require_seller("nope")


def test_delete_seller(storage):
    manager = MemoryManager(storage)
    manager.save_seller(SellerMemory(seller_id="s1", seller_name="ABC Traders"))
    manager.delete_seller("s1")
    assert manager.get_seller("s1") is None
