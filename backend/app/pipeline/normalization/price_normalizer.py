from typing import Any, List
from app.database.models.market_data import RawMarketData
from app.utils.financial_math import get_decimal

def normalize_yahoo_price_data(ticker: str, exchange: str, raw_df: Any) -> List[RawMarketData]:
    """
    Normalizes a pandas DataFrame of OHLCV data from yfinance into RawMarketData models.
    """
    normalized = []
    for date_idx, row in raw_df.iterrows():
        normalized.append(
            RawMarketData(
                ticker=ticker,
                exchange=exchange,
                trade_date=date_idx.date(),
                open_price=get_decimal(row["Open"]),
                high_price=get_decimal(row["High"]),
                low_price=get_decimal(row["Low"]),
                close_price=get_decimal(row["Close"]),
                volume=int(row["Volume"]),
                data_source="yahoo_finance"
            )
        )
    return normalized
