from decimal import Decimal, ROUND_HALF_UP

def format_buy_event(quantity: Decimal, ticker: str, price: Decimal, total: Decimal) -> str:
    price_display = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_display = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (
        f"Purchased {int(quantity)} shares of {ticker} "
        f"at ₹{price_display} per share. "
        f"Total invested: ₹{total_display}."
    )

def format_split_event(
    numerator: int,
    denominator: int,
    quantity_before: Decimal,
    quantity_after: Decimal,
    cost_before: Decimal,
    cost_after: Decimal
) -> str:
    cost_before_display = cost_before.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    cost_after_display = cost_after.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (
        f"Stock split {numerator}:{denominator}. "
        f"Holdings changed from {int(quantity_before)} to {int(quantity_after)} shares. "
        f"Cost basis adjusted from ₹{cost_before_display} to ₹{cost_after_display} per share."
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
    dps_display = dividend_per_share.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    div_received_display = dividend_received.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (
        f"Dividend of ₹{dps_display} per share received on "
        f"{int(quantity)} shares. "
        f"₹{div_received_display} credited."
    )
