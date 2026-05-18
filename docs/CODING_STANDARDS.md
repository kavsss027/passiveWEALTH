# CODING_STANDARDS.md
# Coding Standards — Non-Negotiable Rules for Every Developer

---

## Financial Arithmetic — The Hardest Rule

Use Python `Decimal` for every monetary value and share quantity. No exceptions.

```python
# CORRECT
from decimal import Decimal, ROUND_HALF_UP

quantity = Decimal("100")
price = Decimal("500.00")
total = quantity * price  # Decimal arithmetic

# WRONG — causes binary rounding errors
quantity = 100
price = 500.00
total = quantity * price  # float arithmetic — NEVER DO THIS
```

When accepting numeric values from external sources (API responses, database reads), always convert via string:

```python
# CORRECT — preserves decimal precision
value = Decimal(str(api_response["dividend_amount"]))

# WRONG — float conversion loses precision
value = Decimal(api_response["dividend_amount"])  # if it's a float, precision is already lost
```

Rounding must always use `ROUND_HALF_UP`:
```python
result = value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
```

---

## Async Throughout

All functions that touch the database, make HTTP calls, or call other async functions must be async. No synchronous blocking calls inside async context.

```python
# CORRECT
async def get_corporate_actions(ticker: str) -> list[CorporateAction]:
    async with async_session() as session:
        result = await session.execute(
            select(CorporateAction).where(CorporateAction.ticker == ticker)
        )
        return result.scalars().all()

# WRONG — blocks the event loop
def get_corporate_actions(ticker: str) -> list[CorporateAction]:
    with session() as s:
        return s.query(CorporateAction).filter_by(ticker=ticker).all()
```

---

## Layer Boundaries — The Architecture Must Be Enforced in Code

Import structure enforces architecture. If you find yourself needing to import across boundaries, the design is wrong.

```python
# CORRECT — engine imports only domain objects and utils
from app.core.exceptions import QuantityCalculationError
from app.utils.date_utils import is_before

# WRONG — engine must never import from repositories
from app.database.repositories.corporate_actions_repo import CorporateActionsRepo  # NEVER

# WRONG — router must never import from engines
from app.corporate_actions.split import SplitHandler  # NEVER in a router
```

---

## SQLAlchemy 2.0 Style Only

No legacy 1.x query API.

```python
# CORRECT — 2.0 style
from sqlalchemy import select
result = await session.execute(
    select(CorporateAction)
    .where(CorporateAction.ticker == ticker)
    .order_by(CorporateAction.action_date.asc())
)

# WRONG — legacy style
session.query(CorporateAction).filter_by(ticker=ticker).order_by("action_date").all()
```

---

## Pydantic v2 Style

```python
# CORRECT — v2 style
from pydantic import BaseModel, field_validator

class ReconstructionRequest(BaseModel):
    ticker: str
    buy_date: date
    quantity: int
    buy_price_per_share: Decimal

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_uppercase(cls, v: str) -> str:
        return v.upper().strip()

# WRONG — v1 style
class ReconstructionRequest(BaseModel):
    @validator("ticker")  # v1 decorator — do not use
    def ticker_must_be_uppercase(cls, v):
        return v.upper()
```

---

## Typed Exceptions

Every error in a financial calculation must be a typed exception defined in `core/exceptions.py`. Never raise generic `Exception` or `ValueError` from engine code.

```python
# core/exceptions.py
class PassiveWealthError(Exception):
    """Base exception for all project errors."""
    pass

class QuantityCalculationError(PassiveWealthError):
    """Raised when share quantity reaches zero or invalid state."""
    pass

class InvalidCorporateActionError(PassiveWealthError):
    """Raised when a corporate action has invalid or missing data."""
    pass

class ExDateViolationError(PassiveWealthError):
    """Raised when ex-date logic produces an unexpected result."""
    pass

class DataFetchFailedError(PassiveWealthError):
    """Raised when external data source is unreachable."""
    pass

class InsufficientDataError(PassiveWealthError):
    """Raised when not enough historical data exists to reconstruct."""
    pass
```

---

## Structured Logging

Use structlog. Never use print(). Never use bare logging.info("some message").

```python
import structlog

log = structlog.get_logger()

# CORRECT
log.info("dividend_calculated",
    ticker=ticker,
    ex_date=str(ex_date),
    quantity=str(quantity),
    rate=str(dividend_rate),
    result=str(dividend_received))

log.error("reconstruction_failed",
    ticker=ticker,
    error=str(exc),
    error_type=type(exc).__name__)

# WRONG
print(f"Dividend calculated: {dividend_received}")
logging.info(f"Reconstructed {ticker}")
```

---

## Function and Variable Naming

Financial domain terms must use their correct names. Do not abbreviate.

```python
# CORRECT
dividend_per_share
ex_dividend_date
cost_basis_per_share
cumulative_dividends_received
total_invested
quantity_on_ex_date

# WRONG
div_ps
ex_dt
cb
cum_divs
tot_inv
qty
```

---

## Repository Pattern

Database interaction happens only in repository classes. Services call repositories. Engines never touch repositories.

```python
# CORRECT repository method signature
class CorporateActionsRepository:
    async def get_by_ticker(
        self,
        ticker: str,
        exchange: str,
        from_date: date | None = None
    ) -> list[CorporateAction]:
        ...

# CORRECT — service calling repository
class ReconstructionService:
    def __init__(self, corporate_actions_repo: CorporateActionsRepository):
        self._repo = corporate_actions_repo

    async def reconstruct(self, request: ReconstructionRequest):
        actions = await self._repo.get_by_ticker(
            ticker=request.ticker,
            exchange=request.exchange,
            from_date=request.buy_date
        )
        ...
```

---

## Code Review Requirements

PRs that touch these files require extra scrutiny and a second reviewer before merge:

- Any file in `corporate_actions/`
- Any file in `reconstruction/`
- Any file in `wealth_engine/`
- `database/models/` — schema changes affect all layers
- `core/exceptions.py` — adding exceptions is fine, renaming breaks existing handlers

PRs that touch these files can be reviewed by any one developer:
- `api/v1/routers/`
- `explainability/`
- `timeline/`
- `utils/`
