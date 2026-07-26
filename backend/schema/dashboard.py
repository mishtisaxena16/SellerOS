from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    connected_marketplaces: int
    inventory_items: int
    pending_orders: int
    active_listings: int
    