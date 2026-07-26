from sqlalchemy.orm import Session

from backend.model.marketplace_account import (
    MarketplaceAccount,
)
from backend.ai.connectors_layer import session_store


class MarketplaceService:

    @staticmethod
    def connect_marketplace(
        db: Session,
        seller_id: int,
        platform: str,
        credentials: dict,
    ):
        platform = platform.lower()

        # Upsert, not insert: session_store.register() (below) only ever
        # holds ONE credential set per seller+platform, and is itself
        # documented as "idempotent/overwriting by design" for exactly
        # this reason. A plain insert let the same platform be connected
        # twice, creating two DB rows behind one session_store entry —
        # deleting either row then wiped AI-runtime access to the
        # platform while the dashboard still showed the other row as
        # connected. Reconnecting should just replace credentials.
        account = (
            db.query(MarketplaceAccount)
            .filter(
                MarketplaceAccount.seller_id == seller_id,
                MarketplaceAccount.platform == platform,
            )
            .first()
        )

        if account:
            account.credentials = credentials
        else:
            account = MarketplaceAccount(
                seller_id=seller_id,
                platform=platform,
                credentials=credentials,
            )
            db.add(account)

        db.commit()

        db.refresh(account)

        # This is the actual integration point with the AI runtime.
        # Without this call, the account exists in this DB and shows up
        # in GET /marketplaces, but the Supervisor/Orchestrator has no
        # way to know it exists — every chat query touching this
        # marketplace would still fail with "no marketplace_session
        # attached", identically to before any credentials were saved.
        session_store.register(
            seller_id=str(seller_id),
            platform=platform,
            credentials=credentials,
        )

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

        # Captured before delete+commit: with the session's default
        # expire_on_commit=True, committing a delete expires the
        # instance, so reading account.platform afterwards would try to
        # re-fetch a row that no longer exists and raise
        # ObjectDeletedError instead of clearing the session below.
        platform = account.platform

        db.delete(account)

        db.commit()

        # Mirror the deletion into the AI runtime's session registry —
        # otherwise a "deleted" marketplace account keeps working for
        # chat queries until the process happens to restart.
        session_store.clear(seller_id=str(seller_id), platform=platform)

    @staticmethod
    def restore_all_sessions(db: Session) -> int:
        """
        Re-registers every persisted MarketplaceAccount into session_store
        on process startup. session_store is an in-process registry — it
        starts empty on every restart even though this DB table still has
        every account. Without this, a seller who connected Amazon
        yesterday would silently lose AI-runtime access to it the moment
        the backend process restarts, despite GET /marketplaces still
        showing it as connected. Returns the number of accounts restored.
        """
        accounts = db.query(MarketplaceAccount).all()
        for account in accounts:
            session_store.register(
                seller_id=str(account.seller_id),
                platform=account.platform,
                credentials=account.credentials,
            )
        return len(accounts)