from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import date
from dataclasses import dataclass

@dataclass
class PortfolioState:
    date: date
    quantity: Decimal
    cost_basis_per_share: Decimal
    total_invested: Decimal
    cumulative_dividends_received: Decimal

@dataclass
class ActionResult:
    new_state: PortfolioState
    event_type: str
    description: str
    financial_impact: Decimal
    impact_type: str   # STRUCTURAL, REALIZED, UNREALIZED

class CorporateActionHandler(ABC):
    @abstractmethod
    def apply(self, state: PortfolioState, action: dict) -> ActionResult:
        pass

    @abstractmethod
    def is_eligible(self, buy_date: date, action_date: date) -> bool:
        pass
