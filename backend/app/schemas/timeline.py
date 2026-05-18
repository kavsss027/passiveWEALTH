from pydantic import BaseModel
from datetime import date

class TimelineEntry(BaseModel):
    event_date: date
    event_type: str
    description: str
    quantity_before: int
    quantity_after: int
    financial_impact: str
    impact_type: str
    cumulative_dividends: str
