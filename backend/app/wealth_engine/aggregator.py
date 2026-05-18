from decimal import Decimal, ROUND_HALF_UP

def aggregate_wealth_summary(
    total_dividends: Decimal,
    unrealized_gain: Decimal,
    current_quantity: Decimal,
    current_price: Decimal
) -> dict:
    """
    Combines realized dividends and unrealized appreciation to build the wealth summary.
    """
    current_market_value = current_quantity * current_price
    total_wealth = total_dividends + current_market_value
    
    total_dividends_q = total_dividends.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    unrealized_gain_q = unrealized_gain.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    total_wealth_q = total_wealth.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    
    return {
        "total_dividends_received": str(total_dividends_q),
        "unrealized_gain": str(unrealized_gain_q),
        "unrealized_gain_label": "if sold at current market price",
        "total_wealth_if_sold": str(total_wealth_q),
        "total_wealth_label": "total wealth if all shares sold today including dividends received"
    }
