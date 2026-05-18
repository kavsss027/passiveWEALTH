from datetime import date
from decimal import Decimal
from typing import List, Dict, Any
from app.core.exceptions import ValidationError
from .base import PortfolioState, ActionResult
from .split import StockSplitHandler
from .bonus import BonusIssueHandler
from .dividend import CashDividendHandler

class CorporateActionSequencer:
    def __init__(self):
        self.handlers = {
            "SPLIT": StockSplitHandler(),
            "BONUS": BonusIssueHandler(),
            "DIVIDEND": CashDividendHandler()
        }

    def sort_and_filter(
        self,
        actions: List[Dict[str, Any]],
        buy_date: date
    ) -> List[Dict[str, Any]]:
        """
        Filters out ineligible actions and sorts remaining actions by action_date,
        and then by action_type priority on same-date: SPLIT -> BONUS -> DIVIDEND.
        """
        today = date.today()
        eligible_actions = []
        for action in actions:
            action_type = action["action_type"]
            
            # Filter out future corporate actions
            if action["action_date"] > today:
                continue
                
            handler = self.handlers.get(action_type)
            if not handler:
                # Keep it in eligible actions so engine can log a warning
                eligible_actions.append(action)
                continue
            
            if handler.is_eligible(buy_date, action["action_date"]):
                eligible_actions.append(action)

        priority_map = {
            "SPLIT": 0,
            "BONUS": 1,
            "DIVIDEND": 2
        }

        eligible_actions.sort(
            key=lambda x: (x["action_date"], priority_map.get(x["action_type"], 99))
        )
        return eligible_actions

    def process_timeline(
        self,
        buy_date: date,
        initial_quantity: Decimal,
        buy_price: Decimal,
        actions: List[Dict[str, Any]]
    ) -> List[ActionResult]:
        """
        Processes a timeline of corporate actions starting from a buy event.
        """
        total_invested = initial_quantity * buy_price
        state = PortfolioState(
            date=buy_date,
            quantity=initial_quantity,
            cost_basis_per_share=buy_price,
            total_invested=total_invested,
            cumulative_dividends_received=Decimal("0.0000")
        )

        eligible_actions = self.sort_and_filter(actions, buy_date)

        results = []
        current_state = state
        for action in eligible_actions:
            action_type = action["action_type"]
            handler = self.handlers.get(action_type)
            if not handler:
                raise ValidationError(f"Unsupported action type: {action_type}")
            result = handler.apply(current_state, action)
            results.append(result)
            current_state = result.new_state

        return results
