from sqlalchemy.orm import Session

from backend.model.marketplace_account import (
    MarketplaceAccount,
)


class DashboardService:

    @staticmethod
    def get_summary(
        db: Session,
        seller_id: int,
    ):

        marketplace_count = (
            db.query(MarketplaceAccount)
            .filter(
                MarketplaceAccount.seller_id == seller_id
            )
            .count()
        )

        return {
            "connected_marketplaces": marketplace_count,
            "inventory_items": 156,
            "pending_orders": 18,
            "active_listings": 120,
        }