from decimal import Decimal
from datetime import date
import logging
from app.core.exceptions import ValidationError
from .base import CorporateActionHandler, PortfolioState, ActionResult
from app.explainability.event_formatter import format_split_event

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

        description = format_split_event(
            numerator=int(numerator),
            denominator=int(denominator),
            quantity_before=state.quantity,
            quantity_after=new_quantity,
            cost_before=state.cost_basis_per_share,
            cost_after=new_cost_basis
        )

        return ActionResult(
            new_state=new_state,
            event_type="SPLIT",
            description=description,
            financial_impact=Decimal("0"),
            impact_type="STRUCTURAL"
        )
