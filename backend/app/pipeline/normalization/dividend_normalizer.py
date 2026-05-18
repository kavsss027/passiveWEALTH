from typing import Any, List
from app.database.models.raw_dividends import RawDividend
from app.utils.financial_math import get_decimal

def normalize_yahoo_dividends(ticker: str, exchange: str, raw_dividends: Any) -> List[RawDividend]:
    """
    Normalizes a pandas Series of dividend data from yfinance into RawDividend models.
    """
    normalized = []
    # yfinance dividends is a Series where index is date and value is amount
    for date_idx, amount in raw_dividends.items():
        normalized.append(
            RawDividend(
                ticker=ticker,
                exchange=exchange,
                ex_date=date_idx.date(),
                dividend_amount=get_decimal(amount),
                data_source="yahoo_finance"
            )
        )
    return normalized
