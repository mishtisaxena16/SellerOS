from backend.config.logging import get_logger
from backend.database.base import Base
from backend.database.database import engine

# Import all models so SQLAlchemy can discover them
from backend.model.user import User
from backend.model.seller import Seller
from backend.model.marketplace_account import MarketplaceAccount

logger = get_logger(__name__)


def init_db() -> None:
    """
    Create all database tables.
    """

    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized successfully.")