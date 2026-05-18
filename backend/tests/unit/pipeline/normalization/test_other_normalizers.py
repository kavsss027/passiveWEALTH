import pytest
from datetime import datetime
from decimal import Decimal
import pandas as pd
from app.pipeline.normalization.price_normalizer import normalize_yahoo_price_data
from app.pipeline.normalization.dividend_normalizer import normalize_yahoo_dividends

def test_price_normalizer():
    # Construct a sample pandas DataFrame
    dates = [datetime(2020, 1, 1), datetime(2020, 1, 2)]
    data = {
        "Open": [100.0, 101.0],
        "High": [105.0, 106.0],
        "Low": [95.0, 96.0],
        "Close": [102.0, 103.0],
        "Volume": [1000, 1100]
    }
    df = pd.DataFrame(data, index=dates)
    
    normalized = normalize_yahoo_price_data("INFY", "NSE", df)
    
    assert len(normalized) == 2
    assert normalized[0].ticker == "INFY"
    assert normalized[0].close_price == Decimal("102.0000")
    assert normalized[0].volume == 1000

def test_dividend_normalizer():
    # Construct a sample pandas Series
    dates = [datetime(2020, 1, 1), datetime(2020, 1, 2)]
    series = pd.Series([10.5, 12.0], index=dates)
    
    normalized = normalize_yahoo_dividends("INFY", "NSE", series)
    
    assert len(normalized) == 2
    assert normalized[0].ticker == "INFY"
    assert normalized[0].dividend_amount == Decimal("10.5000")
