from sqlalchemy import String, Date, Numeric, BigInteger, UniqueConstraint, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from decimal import Decimal
from .base import Base, TimestampMixin

class RawDividend(Base, TimestampMixin):
    __tablename__ = "raw_dividends"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False)
    ex_date: Mapped[date] = mapped_column(Date, nullable=False)
    dividend_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    deleted_at: Mapped[date | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("ticker", "exchange", "ex_date", name="uq_dividends_ticker_exdate"),
        Index("idx_dividends_ticker_exdate", "ticker", "ex_date"),
    )
