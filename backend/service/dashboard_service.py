from sqlalchemy.orm import Session

from backend.service.marketplace_data_service import get_dashboard_summary


class DashboardService:

    @staticmethod
    async def get_summary(
        db: Session,
        seller_id: int,
    ):
        return await get_dashboard_summary(db, seller_id)