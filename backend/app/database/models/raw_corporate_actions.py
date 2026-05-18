from sqlalchemy import String, Date, Numeric, BigInteger, UniqueConstraint, Index, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from decimal import Decimal
from typing import Any
from .base import Base, TimestampMixin

class RawCorporateAction(Base, TimestampMixin):
    __tablename__ = "raw_corporate_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False)
    action_date: Mapped[date] = mapped_column(Date, nullable=False)
    action_type_raw: Mapped[str] = mapped_column(String(100), nullable=False)
    numerator: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    denominator: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    deleted_at: Mapped[date | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_raw_actions_ticker_date", "ticker", "action_date"),
    )
