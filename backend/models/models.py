"""
models.py — SellerOS domain models (synced from marketplace_sdk).

These are the ONLY objects that ever leave the connector layer.
Agents, the orchestrator, and everything above the SDK work exclusively
with these — never with raw platform JSON.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class Product(BaseModel):
    platform: str
    sku: str
    listing_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    currency: str = "INR"
    category: Optional[str] = None
    stock_quantity: Optional[int] = None
    status: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class OrderItem(BaseModel):
    sku: str
    quantity: int
    unit_price: Optional[float] = None


class Order(BaseModel):
    platform: str
    order_id: str
    status: str
    items: list[OrderItem] = Field(default_factory=list)
    total_amount: Optional[float] = None
    currency: str = "INR"
    order_date: Optional[datetime] = None
    customer_state: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Inventory(BaseModel):
    platform: str
    sku: str
    available_quantity: int
    reserved_quantity: int = 0
    warehouse: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Campaign(BaseModel):
    platform: str
    campaign_id: str
    name: str
    status: str
    budget: Optional[float] = None
    spend: Optional[float] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Shipment(BaseModel):
    platform: str
    shipment_id: str
    order_id: str
    status: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Account(BaseModel):
    platform: str
    seller_id: str
    seller_name: Optional[str] = None
    is_active: bool = True
    raw: dict[str, Any] = Field(default_factory=dict)
