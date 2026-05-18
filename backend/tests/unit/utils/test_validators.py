import pytest
from app.utils.validators import validate_ticker

def test_validate_ticker_valid():
    assert validate_ticker("INFY") == "INFY"
    assert validate_ticker(" infy ") == "INFY"
    assert validate_ticker("M&M-FIN") == "M&M-FIN" # Oh wait, M&M has ampersand. We should allow ampersand?

def test_validate_ticker_invalid():
    with pytest.raises(ValueError):
        validate_ticker("INFY@")
