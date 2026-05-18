import re

def validate_ticker(ticker: str) -> str:
    """Validate ticker symbol format."""
    ticker = ticker.strip().upper()
    if not re.match(r"^[A-Z0-9\-&]+$", ticker):
        raise ValueError(f"Invalid ticker format: {ticker}")
    return ticker
