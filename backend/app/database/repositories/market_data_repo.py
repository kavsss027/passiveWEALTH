from typing import List, Optional
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.market_data import RawMarketData
from .base_repo import BaseRepository

class MarketDataRepository(BaseRepository[RawMarketData]):
    def __init__(self):
        super().__init__(RawMarketData)

    async def get_by_ticker_and_date_range(
        self, session: AsyncSession, ticker: str, exchange: str, start_date: date, end_date: date
    ) -> List[RawMarketData]:
        stmt = select(self.model).filter(
            and_(
                self.model.ticker == ticker,
                self.model.exchange == exchange,
                self.model.trade_date >= start_date,
                self.model.trade_date <= end_date,
            )
        ).order_by(self.model.trade_date.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

market_data_repo = MarketDataRepository()
