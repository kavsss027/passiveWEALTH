from decimal import Decimal, ROUND_HALF_UP
from typing import Union

def get_decimal(value: Union[str, int, float, Decimal]) -> Decimal:
    """Safely convert any numeric type to Decimal."""
    if isinstance(value, Decimal):
        return value
    try:
        f_val = float(value)
        if f_val.is_integer():
            return Decimal(str(int(f_val)))
        return Decimal(str(round(f_val, 4)))
    except (ValueError, TypeError):
        return Decimal(str(value))

def round_monetary(value: Decimal) -> Decimal:
    """Round to 4 decimal places for monetary values."""
    return value.quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)

def calculate_adjusted_cost_basis(original_cost: Decimal, ratio: Decimal) -> Decimal:
    """Calculate new cost basis after a corporate action."""
    return round_monetary(original_cost / ratio)

def calculate_shares_after_action(original_shares: Decimal, ratio: Decimal) -> Decimal:
    """Calculate new number of shares after a corporate action."""
    return round_monetary(original_shares * ratio)
