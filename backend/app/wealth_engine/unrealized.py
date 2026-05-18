from decimal import Decimal

def calculate_unrealized_gain(
    current_price: Decimal,
    adjusted_cost_basis: Decimal,
    current_quantity: Decimal
) -> Decimal:
    """
    Calculates unrealized gain as:
    (current_price - adjusted_cost_basis) * current_quantity
    """
    return (current_price - adjusted_cost_basis) * current_quantity
