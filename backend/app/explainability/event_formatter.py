from decimal import Decimal

def format_buy_event(quantity: Decimal, ticker: str, price: Decimal, total: Decimal) -> str:
    return (
        f"Purchased {int(quantity)} shares of {ticker} "
        f"at ₹{price} per share. "
        f"Total invested: ₹{total}."
    )

def format_split_event(
    numerator: int,
    denominator: int,
    quantity_before: Decimal,
    quantity_after: Decimal,
    cost_before: Decimal,
    cost_after: Decimal
) -> str:
    return (
        f"Stock split {numerator}:{denominator}. "
        f"Holdings changed from {int(quantity_before)} to {int(quantity_after)} shares. "
        f"Cost basis adjusted from ₹{cost_before} to ₹{cost_after} per share."
    )

def format_bonus_event(
    numerator: int,
    denominator: int,
    additional_shares: Decimal,
    quantity_before: Decimal,
    quantity_after: Decimal
) -> str:
    return (
        f"Bonus issue {numerator}:{denominator}. "
        f"{int(additional_shares)} additional shares issued. "
        f"Holdings increased from {int(quantity_before)} to {int(quantity_after)} shares."
    )

def format_dividend_event(
    dividend_per_share: Decimal,
    quantity: Decimal,
    dividend_received: Decimal
) -> str:
    return (
        f"Dividend of ₹{dividend_per_share} per share received on "
        f"{int(quantity)} shares. "
        f"₹{dividend_received} credited."
    )
