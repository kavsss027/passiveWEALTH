import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from app.pipeline.ingestion.yahoo_finance import fetch_yahoo_finance_data
from app.core.exceptions import DataIngestionError

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.yahoo_finance.yf.Ticker")
async def test_fetch_yahoo_finance_data_success(mock_ticker):
    mock_instance = MagicMock()
    mock_instance.history.return_value = "mock_hist"
    mock_instance.dividends = "mock_dividends"
    mock_instance.splits = "mock_splits"
    mock_ticker.return_value = mock_instance
    
    result = await fetch_yahoo_finance_data("INFY", date(2020, 1, 1), date(2020, 1, 31))
    
    assert result["hist"] == "mock_hist"
    assert result["dividends"] == "mock_dividends"
    assert result["splits"] == "mock_splits"
    mock_instance.history.assert_called_once_with(start="2020-01-01", end="2020-01-31", auto_adjust=False)

@pytest.mark.asyncio
@patch("app.pipeline.ingestion.yahoo_finance.yf.Ticker")
async def test_fetch_yahoo_finance_data_failure(mock_ticker):
    mock_ticker.side_effect = Exception("API error")
    
    with pytest.raises(DataIngestionError) as exc:
        await fetch_yahoo_finance_data("INFY", date(2020, 1, 1), date(2020, 1, 31))
    
    assert "Failed to fetch Yahoo Finance data for INFY" in str(exc.value)
