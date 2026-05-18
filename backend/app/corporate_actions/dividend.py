from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from app.core.exceptions import ValidationError
from .base import CorporateActionHandler, PortfolioState, ActionResult

class CashDividendHandler(CorporateActionHandler):
    def is_eligible(self, buy_date: date, action_date: date) -> bool:
        # Eligible only if buy_date < ex_date (strictly less than)
        return buy_date < action_date

    def apply(self, state: PortfolioState, action: dict) -> ActionResult:
        dividend_per_share = Decimal(str(action["numerator"]))

        if dividend_per_share <= 0:
            raise ValidationError("Dividend per share must be positive")

        # Use quantity at the ex-date
        dividend_received = state.quantity * dividend_per_share
        dividend_received = dividend_received.quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        new_cumulative = state.cumulative_dividends_received + dividend_received

        new_state = PortfolioState(
            date=action["action_date"],
            quantity=state.quantity,
            cost_basis_per_share=state.cost_basis_per_share,
            total_invested=state.total_invested,
            cumulative_dividends_received=new_cumulative
        )

        description = (
            f"Dividend of ₹{dividend_per_share} per share received on "
            f"{state.quantity} shares. ₹{dividend_received} credited."
        )

        return ActionResult(
            new_state=new_state,
            event_type="DIVIDEND",
            description=description,
            financial_impact=dividend_received,
            impact_type="REALIZED"
        )
