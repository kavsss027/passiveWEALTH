from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_db
from app.database.repositories.corporate_actions_repo import corporate_actions_repo
from app.core.exceptions import AppError
from pydantic import BaseModel

router = APIRouter()

class CorporateActionResponseItem(BaseModel):
    action_date: date
    action_type: str
    numerator: int
    denominator: int
    data_source: str
    confidence: str

class CorporateActionsResponse(BaseModel):
    ticker: str
    exchange: str
    total_count: int
    actions: List[CorporateActionResponseItem]

@router.get("/{ticker}", response_model=CorporateActionsResponse)
async def get_corporate_actions(
    ticker: str,
    exchange: str = Query("NSE"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_db)
):
    valid_tickers = {"INFY", "TCS", "RELIANCE"}
    if ticker.upper() not in valid_tickers:
        raise AppError(f"Ticker {ticker} not found", code="INVALID_TICKER")

    actions = await corporate_actions_repo.get_by_ticker(session, ticker.upper(), exchange)
    
    # Filter by dates
    filtered_actions = []
    for action in actions:
        if from_date and action.action_date < from_date:
            continue
        if to_date and action.action_date > to_date:
            continue
        filtered_actions.append(
            CorporateActionResponseItem(
                action_date=action.action_date,
                action_type=action.action_type,
                numerator=action.numerator,
                denominator=action.denominator,
                data_source=action.data_source,
                confidence=action.confidence
            )
        )

    return CorporateActionsResponse(
        ticker=ticker.upper(),
        exchange=exchange,
        total_count=len(filtered_actions),
        actions=filtered_actions
    )
