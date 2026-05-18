from decimal import Decimal
from datetime import date
from app.corporate_actions.base import PortfolioState, ActionResult, CorporateActionHandler
from app.reconstruction.quantity_tracker import QuantityTracker

class PortfolioStateMachine:
    def __init__(
        self,
        buy_date: date,
        quantity: Decimal,
        buy_price_per_share: Decimal
    ):
        self.current_state = PortfolioState(
            date=buy_date,
            quantity=quantity,
            cost_basis_per_share=buy_price_per_share,
            total_invested=quantity * buy_price_per_share,
            cumulative_dividends_received=Decimal("0.0000")
        )
        self.state_history: list[PortfolioState] = [self.current_state]
        self.event_log: list[ActionResult] = []
        self.quantity_tracker = QuantityTracker(buy_date, quantity)

    def apply(self, handler: CorporateActionHandler, action: dict) -> ActionResult:
        # Check eligibility using initial state date (or current state date)
        # Note: handlers' eligibility typically checks the buy_date (which is in current_state.date or self.state_history[0].date).
        # To match the sequencer/handler specification perfectly: buy_date = self.state_history[0].date
        buy_date = self.state_history[0].date
        if not handler.is_eligible(buy_date, action["action_date"]):
            return None  # Skip ineligible actions silently

        result = handler.apply(self.current_state, action)
        
        # Record structural changes in quantity tracker
        if result.event_type in ("SPLIT", "BONUS"):
            self.quantity_tracker.record_change(
                action["action_date"],
                result.new_state.quantity,
                result.event_type
            )

        self.current_state = result.new_state
        self.state_history.append(result.new_state)
        self.event_log.append(result)
        return result

    def final_state(self) -> PortfolioState:
        return self.current_state

    def full_event_log(self) -> list[ActionResult]:
        return self.event_log
