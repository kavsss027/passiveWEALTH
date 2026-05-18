from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List
from decimal import Decimal
from app.schemas.wealth import CurrentState, WealthSummary
from app.schemas.timeline import TimelineEntry

class DataQuality(BaseModel):
    confidence: str
    sources_used: List[str]
    warnings: List[str]

from typing import Optional

class PortfolioReconstructRequest(BaseModel):
    ticker: str
    exchange: str
    buy_date: date
    quantity: int = Field(gt=0)
    total_amount_invested: Optional[Decimal] = Field(default=None, gt=0)


    @field_validator("exchange")
    def validate_exchange(cls, v):
        if v not in ["NSE", "BSE"]:
            raise ValueError("Exchange must be NSE or BSE")
        return v
    
    @field_validator("buy_date")
    def validate_buy_date(cls, v):
        if v > date.today():
            raise ValueError("buy_date is in the future")
        if v < date(1990, 1, 1):
            raise ValueError("buy_date is before 1990")
        return v

class PortfolioReconstructResponse(BaseModel):
    ticker: str
    exchange: str
    buy_date: date
    original_quantity: int
    original_investment: str
    current_state: CurrentState
    wealth_summary: WealthSummary
    timeline: List[TimelineEntry]
    data_quality: DataQuality
