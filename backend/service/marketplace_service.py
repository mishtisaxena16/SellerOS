from sqlalchemy.orm import Session

from backend.model.marketplace_account import (
    MarketplaceAccount,
)


class MarketplaceService:

    @staticmethod
    def connect_marketplace(
        db: Session,
        seller_id: int,
        platform: str,
        credentials: dict,
    ):

        account = MarketplaceAccount(
            seller_id=seller_id,
            platform=platform.lower(),
            credentials=credentials,
        )

        db.add(account)

        db.commit()

        db.refresh(account)

        return account

    @staticmethod
    def get_marketplaces(
        db: Session,
        seller_id: int,
    ):

        return (
            db.query(MarketplaceAccount)
            .filter(
                MarketplaceAccount.seller_id == seller_id
            )
            .all()
        )

    @staticmethod
    def delete_marketplace(
        db: Session,
        seller_id: int,
        marketplace_id: int,
    ):

        account = (
            db.query(MarketplaceAccount)
            .filter(
                MarketplaceAccount.id == marketplace_id,
                MarketplaceAccount.seller_id == seller_id,
            )
            .first()
        )

        if not account:
            raise ValueError(
                "Marketplace account not found."
            )

        db.delete(account)

        db.commit()