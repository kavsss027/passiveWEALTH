from typing import List, Optional
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.corporate_actions import CorporateAction
from app.database.models.raw_corporate_actions import RawCorporateAction
from .base_repo import BaseRepository

class CorporateActionsRepository(BaseRepository[CorporateAction]):
    def __init__(self):
        super().__init__(CorporateAction)

    async def get_by_ticker(
        self, session: AsyncSession, ticker: str, exchange: str
    ) -> List[CorporateAction]:
        stmt = select(self.model).filter(
            and_(
                self.model.ticker == ticker,
                self.model.exchange == exchange,
            )
        ).order_by(self.model.action_date.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

class RawCorporateActionsRepository(BaseRepository[RawCorporateAction]):
    def __init__(self):
        super().__init__(RawCorporateAction)

    async def get_unprocessed(self, session: AsyncSession) -> List[RawCorporateAction]:
        # For simplicity, returning all for now, but usually would have a processed flag
        stmt = select(self.model).order_by(self.model.action_date.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

corporate_actions_repo = CorporateActionsRepository()
raw_corporate_actions_repo = RawCorporateActionsRepository()
