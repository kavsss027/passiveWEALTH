from decimal import Decimal

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
    
    return {
        "total_dividends_received": str(total_dividends),
        "unrealized_gain": str(unrealized_gain),
        "unrealized_gain_label": "if sold at current market price",
        "total_wealth_if_sold": str(total_wealth),
        "total_wealth_label": "total wealth if all shares sold today including dividends received"
    }
