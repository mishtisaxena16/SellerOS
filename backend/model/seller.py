from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Seller(Base):
    """
    Seller account model.

    This is the business identity inside SellerOS.

    IMPORTANT:
    The AI Engine requires a valid seller_id for all
    supervisor operations.
    """

    __tablename__ = "sellers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="seller",
    )

    def __repr__(self) -> str:
        return (
            f"Seller("
            f"id={self.id}, "
            f"business_name='{self.business_name}'"
            f")"
        )
