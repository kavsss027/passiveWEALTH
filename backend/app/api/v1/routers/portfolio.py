from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_db, get_timeline_service
from app.services.timeline_service import TimelineService
from app.schemas.portfolio import PortfolioReconstructRequest, PortfolioReconstructResponse
from app.core.exceptions import AppError

router = APIRouter()

@router.post("/reconstruct", response_model=PortfolioReconstructResponse)
async def reconstruct_portfolio(
    request: PortfolioReconstructRequest,
    session: AsyncSession = Depends(get_db),
    timeline_service: TimelineService = Depends(get_timeline_service)
):
    # Validate ticker is not empty
    if not request.ticker or len(request.ticker.strip()) < 2:
        raise AppError("Ticker symbol must be at least 2 characters long", code="INVALID_TICKER")

    try:
        response = await timeline_service.generate_timeline(
            session=session,
            ticker=request.ticker.upper(),
            exchange=request.exchange,
            buy_date=request.buy_date,
            quantity=request.quantity,
            total_amount_invested=request.total_amount_invested
        )
        return response
    except Exception as e:
        if hasattr(e, "code"):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

