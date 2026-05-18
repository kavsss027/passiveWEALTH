import pytest
from datetime import date, timedelta
from decimal import Decimal
from pydantic import ValidationError
from app.schemas.portfolio import PortfolioReconstructRequest

def test_portfolio_request_valid():
    req = PortfolioReconstructRequest(
        ticker="INFY",
        exchange="NSE",
        buy_date=date(2000, 1, 15),
        quantity=100,
        total_amount_invested=Decimal("50000.00")
    )
    assert req.ticker == "INFY"
    assert req.exchange == "NSE"

def test_portfolio_request_valid_optional():
    req = PortfolioReconstructRequest(
        ticker="INFY",
        exchange="NSE",
        buy_date=date(2000, 1, 15),
        quantity=100
    )
    assert req.total_amount_invested is None

def test_portfolio_request_invalid_exchange():
    with pytest.raises(ValidationError):
        PortfolioReconstructRequest(
            ticker="INFY",
            exchange="NYQ",
            buy_date=date(2000, 1, 15),
            quantity=100,
            total_amount_invested=Decimal("50000.00")
        )

def test_portfolio_request_future_date():
    with pytest.raises(ValidationError):
        PortfolioReconstructRequest(
            ticker="INFY",
            exchange="NSE",
            buy_date=date.today() + timedelta(days=1),
            quantity=100,
            total_amount_invested=Decimal("50000.00")
        )

def test_portfolio_request_before_1990():
    with pytest.raises(ValidationError):
        PortfolioReconstructRequest(
            ticker="INFY",
            exchange="NSE",
            buy_date=date(1989, 12, 31),
            quantity=100,
            total_amount_invested=Decimal("50000.00")
        )

def test_portfolio_request_invalid_quantity():
    with pytest.raises(ValidationError):
        PortfolioReconstructRequest(
            ticker="INFY",
            exchange="NSE",
            buy_date=date(2000, 1, 15),
            quantity=0,
            total_amount_invested=Decimal("50000.00")
        )

def test_portfolio_request_invalid_total_amount():
    with pytest.raises(ValidationError):
        PortfolioReconstructRequest(
            ticker="INFY",
            exchange="NSE",
            buy_date=date(2000, 1, 15),
            quantity=100,
            total_amount_invested=Decimal("-10.0")
        )
