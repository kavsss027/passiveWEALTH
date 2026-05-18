from sqlalchemy import String, Date, Numeric, BigInteger, UniqueConstraint, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from .base import Base, TimestampMixin

from decimal import Decimal

class RawMarketData(Base, TimestampMixin):
    __tablename__ = "raw_market_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    deleted_at: Mapped[date | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("ticker", "exchange", "trade_date", name="uq_market_data_ticker_date"),
        Index("idx_market_data_ticker_date", "ticker", "trade_date"),
    )
