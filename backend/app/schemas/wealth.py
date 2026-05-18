from pydantic import BaseModel

class CurrentState(BaseModel):
    quantity: int
    current_price_per_share: str
    current_market_value: str
    adjusted_cost_basis_per_share: str
    total_invested: str

class WealthSummary(BaseModel):
    total_dividends_received: str
    unrealized_gain: str
    unrealized_gain_label: str
    total_wealth_if_sold: str
    wealth_multiple: str
