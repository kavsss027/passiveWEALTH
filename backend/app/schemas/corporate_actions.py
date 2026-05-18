from pydantic import BaseModel
from datetime import date
from typing import List
from decimal import Decimal

class CorporateActionResponse(BaseModel):
    action_date: date
    action_type: str
    numerator: Decimal
    denominator: Decimal
    data_source: str
    confidence: str

class CorporateActionsListResponse(BaseModel):
    ticker: str
    exchange: str
    total_count: int
    actions: List[CorporateActionResponse]
