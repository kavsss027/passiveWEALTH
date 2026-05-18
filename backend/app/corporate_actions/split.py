from decimal import Decimal
from datetime import date
import logging
from app.core.exceptions import ValidationError
from .base import CorporateActionHandler, PortfolioState, ActionResult

logger = logging.getLogger(__name__)

class StockSplitHandler(CorporateActionHandler):
    def is_eligible(self, buy_date: date, action_date: date) -> bool:
        return buy_date < action_date

    def apply(self, state: PortfolioState, action: dict) -> ActionResult:
        numerator = Decimal(str(action["numerator"]))
        denominator = Decimal(str(action["denominator"]))

        if numerator == denominator:
            raise ValidationError("Split numerator cannot equal denominator")
        if numerator <= 0 or denominator <= 0:
            raise ValidationError("Split numerator and denominator must be positive")

        if numerator < denominator:
            logger.warning(f"Reverse stock split encountered: {numerator}:{denominator}")

        split_ratio = numerator / denominator
        new_quantity = state.quantity * split_ratio

        # Total invested never changes for structural events
        new_cost_basis = state.total_invested / new_quantity

        new_state = PortfolioState(
            date=action["action_date"],
            quantity=new_quantity,
            cost_basis_per_share=new_cost_basis,
            total_invested=state.total_invested,
            cumulative_dividends_received=state.cumulative_dividends_received
        )

        description = (
            f"Stock split {int(numerator)}:{int(denominator)}. "
            f"Holdings changed from {state.quantity} to {new_quantity} shares. "
            f"Cost basis adjusted from ₹{state.cost_basis_per_share} to ₹{new_cost_basis} per share."
        )

        return ActionResult(
            new_state=new_state,
            event_type="SPLIT",
            description=description,
            financial_impact=Decimal("0"),
            impact_type="STRUCTURAL"
        )
