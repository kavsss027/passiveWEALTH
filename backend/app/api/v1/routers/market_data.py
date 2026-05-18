from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_db
from app.database.repositories.market_data_repo import market_data_repo
from app.core.exceptions import AppError
from pydantic import BaseModel

router = APIRouter()

class PriceItem(BaseModel):
    trade_date: date
    open: str
    high: str
    low: str
    close: str
    volume: int

class MarketDataResponse(BaseModel):
    ticker: str
    exchange: str
    from_date: date
    to_date: date
    data_points: int
    prices: List[PriceItem]

@router.get("/{ticker}", response_model=MarketDataResponse)
async def get_market_data(
    ticker: str,
    from_date: date = Query(...),
    to_date: date = Query(...),
    exchange: str = Query("NSE"),
    session: AsyncSession = Depends(get_db)
):
    valid_tickers = {"INFY", "TCS", "RELIANCE"}
    if ticker.upper() not in valid_tickers:
        raise AppError(f"Ticker {ticker} not found", code="INVALID_TICKER")

    prices = await market_data_repo.get_by_ticker_and_date_range(
        session, ticker.upper(), exchange, from_date, to_date
    )
    
    if not prices:
        raise AppError(f"No market data found for ticker {ticker} in range {from_date} to {to_date}", code="NOT_FOUND")

    price_items = []
    for price in prices:
        price_items.append(
            PriceItem(
                trade_date=price.trade_date,
                open=str(price.open),
                high=str(price.high),
                low=str(price.low),
                close=str(price.close),
                volume=int(price.volume)
            )
        )

    return MarketDataResponse(
        ticker=ticker.upper(),
        exchange=exchange,
        from_date=from_date,
        to_date=to_date,
        data_points=len(price_items),
        prices=price_items
    )
