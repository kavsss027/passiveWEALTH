from decimal import Decimal
from datetime import date
import logging
from app.core.exceptions import ValidationError
from .base import CorporateActionHandler, PortfolioState, ActionResult
from app.explainability.event_formatter import format_bonus_event

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

        description = format_bonus_event(
            numerator=int(numerator),
            denominator=int(denominator),
            additional_shares=additional_shares,
            quantity_before=state.quantity,
            quantity_after=new_quantity
        )

        return ActionResult(
            new_state=new_state,
            event_type="BONUS",
            description=description,
            financial_impact=Decimal("0"),
            impact_type="STRUCTURAL"
        )
