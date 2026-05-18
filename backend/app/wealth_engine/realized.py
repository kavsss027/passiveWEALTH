from decimal import Decimal
from typing import List
from app.corporate_actions.base import ActionResult

def calculate_realized_dividends(event_log: List[ActionResult]) -> Decimal:
    """
    Sums all ActionResults where impact_type == "REALIZED"
    """
    total = Decimal("0.0000")
    for result in event_log:
        if result.impact_type == "REALIZED":
            total += result.financial_impact
    return total
