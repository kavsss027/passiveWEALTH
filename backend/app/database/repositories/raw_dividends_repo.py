from typing import List, Optional
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.raw_dividends import RawDividend
from .base_repo import BaseRepository

class RawDividendsRepository(BaseRepository[RawDividend]):
    def __init__(self):
        super().__init__(RawDividend)

    async def get_by_ticker(
        self, session: AsyncSession, ticker: str, exchange: str
    ) -> List[RawDividend]:
        stmt = select(self.model).filter(
            and_(
                self.model.ticker == ticker,
                self.model.exchange == exchange,
            )
        ).order_by(self.model.ex_date.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

raw_dividends_repo = RawDividendsRepository()
