from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from backend.database.base import Base


class MarketplaceAccount(Base):
    """
    Connected marketplace account.

    Stores credentials and connection metadata
    for Amazon, Flipkart, Meesho, etc.
    """

    __tablename__ = "marketplace_accounts"

    # Second line of defense against duplicate rows for the same
    # seller+platform (the service layer's upsert is the first line).
    # session_store only ever holds ONE credential set per seller+
    # platform, so two DB rows for the same pair means one of them is
    # always a silent lie: whichever row you delete, the other one
    # keeps showing "connected" in the dashboard while the AI runtime's
    # session is actually gone.
    __table_args__ = (
        UniqueConstraint("seller_id", "platform", name="uq_marketplace_seller_platform"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey("sellers.id"),
        nullable=False,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    credentials: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    seller = relationship(
        "Seller",
        backref="marketplace_accounts",
    )

    def __repr__(self) -> str:
        return (
            f"MarketplaceAccount("
            f"id={self.id}, "
            f"platform='{self.platform}'"
            f")"
        )