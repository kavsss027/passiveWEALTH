from decimal import Decimal
from datetime import date
import logging
from app.core.exceptions import ValidationError
from .base import CorporateActionHandler, PortfolioState, ActionResult

logger = logging.getLogger(__name__)

class BonusIssueHandler(CorporateActionHandler):
    def is_eligible(self, buy_date: date, action_date: date) -> bool:
        return buy_date < action_date

    def apply(self, state: PortfolioState, action: dict) -> ActionResult:
        numerator = Decimal(str(action["numerator"]))
        denominator = Decimal(str(action["denominator"]))

        if numerator <= 0 or denominator <= 0:
            raise ValidationError("Bonus numerator and denominator must be positive")

        # Bonus ratio: numerator shares issued FOR EVERY denominator shares held
        additional_shares = state.quantity * (numerator / denominator)
        new_quantity = state.quantity + additional_shares

        # Total invested does not change — bonus shares are free
        new_cost_basis = state.total_invested / new_quantity

        new_state = PortfolioState(
            date=action["action_date"],
            quantity=new_quantity,
            cost_basis_per_share=new_cost_basis,
            total_invested=state.total_invested,
            cumulative_dividends_received=state.cumulative_dividends_received
        )

        description = (
            f"Bonus issue {int(numerator)}:{int(denominator)}. "
            f"{additional_shares} additional shares issued. "
            f"Holdings increased from {state.quantity} to {new_quantity} shares."
        )

        return ActionResult(
            new_state=new_state,
            event_type="BONUS",
            description=description,
            financial_impact=Decimal("0"),
            impact_type="STRUCTURAL"
        )
