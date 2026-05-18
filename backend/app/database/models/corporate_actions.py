from sqlalchemy import String, Date, Numeric, BigInteger, UniqueConstraint, Index, DateTime, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from decimal import Decimal
from .base import Base, TimestampMixin

class CorporateAction(Base, TimestampMixin):
    __tablename__ = "corporate_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False)
    action_date: Mapped[date] = mapped_column(Date, nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    numerator: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    denominator: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    deleted_at: Mapped[date | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("ticker", "exchange", "action_date", "action_type", name="uq_corporate_actions"),
        CheckConstraint("action_type IN ('SPLIT', 'BONUS', 'DIVIDEND')", name="chk_action_type"),
        Index("idx_corporate_actions_ticker_date", "ticker", "action_date"),
    )
