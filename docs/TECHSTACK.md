# TECHSTACK.md
# Technology Stack — Decisions and Rationale

---

## Every decision in this document is locked for V1.
## Do not introduce new dependencies without updating this document first.

---

## Language

**Python 3.11**

Not 3.12 — library compatibility across pandas, SQLAlchemy 2.0, and FastAPI is most stable at 3.11. Not 3.10 — missing performance improvements. Lock the version in `.python-version` at project root.

---

## Dependency Management

**Poetry**

Not pip + requirements.txt. Poetry's `poetry.lock` file guarantees identical dependency resolution across all environments. Every developer and the CI pipeline get byte-identical installs.

Commands:
```
poetry install          # install all dependencies
poetry add <package>    # add a dependency
poetry add --group dev <package>  # add a dev-only dependency
poetry run pytest       # run inside the poetry environment
```

---

## Backend Framework

**FastAPI — latest stable**

Async-native, automatic OpenAPI docs at /docs, Pydantic v2 integration built in, strong typing support. All route handlers must be async.

**Pydantic v2 — not v1**

v2 is significantly faster on serialization. Timeline responses can be large — serialization speed matters. Never use Pydantic v1 syntax.

---

## Database

**PostgreSQL 15**

Run exclusively via Docker for local development. Never install PostgreSQL directly on the host machine.

Connection: async via `asyncpg` driver managed by SQLAlchemy's async engine.

**SQLAlchemy 2.0 — async style only**

Use the 2.0 unified API. Never use the legacy 1.x style query API. All sessions must be async.

```python
# Correct — 2.0 style
async with async_session() as session:
    result = await session.execute(select(CorporateAction).where(...))

# Wrong — never use this
session.query(CorporateAction).filter(...).all()
```

**Alembic**

All schema changes via Alembic migration files. No manual DDL in production or development. Every migration file gets a descriptive message.

---

## Financial Arithmetic

**Python `Decimal` — mandatory for all monetary values and share quantities**

Float arithmetic produces binary rounding errors that compound across thousands of calculations. This is non-negotiable.

```python
from decimal import Decimal, ROUND_HALF_UP

# Correct
dividend = Decimal("2.50") * Decimal(str(quantity))

# Wrong — never do this
dividend = 2.50 * quantity
```

Rounding rule: always `ROUND_HALF_UP` to match standard Indian financial rounding conventions.

PostgreSQL column type for all monetary values and quantities: `NUMERIC(20, 4)`
Never use `FLOAT` or `DOUBLE PRECISION` for financial data in the database.

---

## Configuration Management

**pydantic-settings**

All environment variables are defined as a Pydantic Settings class in `core/config.py`. Type-validated at startup. Application fails fast if required config is missing.

`.env` — local values, gitignored
`.env.example` — committed to repo, all keys with empty values, documents what is required

---

## Logging

**structlog**

Every log event for a financial calculation must carry structured fields:
```python
log.info("dividend_calculated",
    ticker=ticker,
    ex_date=str(ex_date),
    quantity=str(quantity),
    rate=str(dividend_rate),
    result=str(dividend_received))
```

Plain string logs are not acceptable for financial operations. They cannot be queried or filtered when debugging wrong calculations.

---

## Testing

**pytest + pytest-asyncio + factory-boy**

- `pytest` — test runner
- `pytest-asyncio` — handles async test functions
- `factory-boy` — generates structured test fixtures for financial objects

All financial tests use fixed seed data. No random values in financial test cases. See TESTING_GUIDE.md.

---

## Containerisation

**Docker + Docker Compose**

Docker Compose manages PostgreSQL locally. FastAPI runs outside Docker during development for faster iteration but can be containerised for showcase purposes.

```yaml
# docker-compose.yml manages:
services:
  db:
    image: postgres:15
  # FastAPI runs locally via: poetry run uvicorn app.main:app --reload
```

---

## Data Sources

**Yahoo Finance — via yfinance library**

Used for: historical OHLC prices, dividend history, split/bonus ratio history.

Limitation: does not distinguish between bonus issues and stock splits. Both appear as splits. NSE is used to resolve this.

**NSE India — scraped via requests + session management**

Used for: corporate action type classification (BONUS vs SPLIT vs DIVIDEND), official ex-dates, official ratios.

NSE requires a session cookie. The scraper must hit the NSE homepage first to establish a valid session before calling any data endpoints. See DATA_SOURCES.md for implementation details.

**BSE India — scraped**

Used for: cross-validation of corporate action data when NSE data appears inconsistent. Not a primary source.

---

## What Was Considered and Rejected

**Redis** — removed. Only needed as a Celery broker and cross-session cache. Neither applies to a local stateless single-user system. In-process `lru_cache` is sufficient.

**Celery** — removed. Distributed background job processing is not needed for local use. All processing is synchronous per request.

**Tortoise ORM / SQLModel** — rejected. SQLAlchemy 2.0 provides more control over query generation, which matters for financial data correctness.

**httpx** — use instead of requests for async HTTP calls to NSE and BSE. All external HTTP calls must be async to not block the event loop.

**JWT / Auth** — not built. No user layer in V1.
