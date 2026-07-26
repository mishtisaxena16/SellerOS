from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy import String
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