# TESTING_GUIDE.md
# Testing Guide — Standards, Structure, and Financial Test Rules

---

## Core Testing Philosophy

This is a financial correctness system. Tests are not optional and not decorative. A bug in the reconstruction engine produces wrong rupee values that look correct. The only defense against this is a comprehensive test suite built on real historical data with verified expected outputs.

---

## Testing Stack

```
pytest              test runner
pytest-asyncio      async test support
factory-boy         test fixture generation
pytest-cov          coverage reporting
```

Install via:
```bash
poetry install --with dev
```

---

## Test Directory Structure

```
tests/
├── conftest.py                     shared fixtures and session setup
├── fixtures/
│   ├── corporate_actions.py        factory-boy factories for action objects
│   ├── portfolio_states.py         factory-boy factories for state objects
│   └── real_historical_data.py     hardcoded verified real-world test cases
│
├── unit/
│   ├── corporate_actions/
│   │   ├── test_split_handler.py
│   │   ├── test_bonus_handler.py
│   │   ├── test_dividend_handler.py
│   │   └── test_sequencer.py
│   ├── reconstruction/
│   │   ├── test_quantity_tracker.py
│   │   ├── test_state_machine.py
│   │   └── test_engine.py
│   ├── wealth_engine/
│   │   ├── test_realized.py
│   │   └── test_unrealized.py
│   ├── explainability/
│   │   └── test_event_formatter.py
│   └── pipeline/
│       └── test_normalization.py
│
└── integration/
    ├── test_full_reconstruction_infy.py
    ├── test_full_reconstruction_tcs.py
    └── test_api_endpoints.py
```

---

## The Most Important Rule — Fixed Seed Data

Financial tests must use fixed, hardcoded input values with verified expected outputs.

Never use:
- `random.randint()` for quantities
- `datetime.today()` for dates
- Faker for financial values
- Any non-deterministic value in a financial assertion

Every financial test must read like a paper calculation that another person can verify with a calculator.

```python
# CORRECT — fixed values, verifiable by hand
def test_split_calculation():
    state = PortfolioState(
        date=date(2000, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("500.00"),
        total_invested=Decimal("50000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )
    action = {
        "action_date": date(2004, 6, 1),
        "action_type": "SPLIT",
        "numerator": Decimal("2"),
        "denominator": Decimal("1")
    }
    result = SplitHandler().apply(state, action)

    assert result.new_state.quantity == Decimal("200")
    assert result.new_state.cost_basis_per_share == Decimal("250.00")
    assert result.new_state.total_invested == Decimal("50000.00")
    assert result.financial_impact == Decimal("0")
    assert result.impact_type == "STRUCTURAL"

# WRONG — do not do this
def test_split_calculation():
    quantity = random.randint(50, 500)  # NEVER
    ...
```

---

## Real Historical Test Cases — Use These

These are verified real corporate actions from Indian stocks. Use them as integration test inputs with known expected outputs.

### Infosys (INFY.NS)

| Event | Date | Detail |
|---|---|---|
| Split | Jun 2004 | 2:1 split |
| Split | Jun 1999 | 2:1 split |
| Bonus | Jun 2018 | 1:1 bonus |
| Bonus | Jun 2014 | 1:1 bonus |

**Integration test scenario — INFY:**
```
Buy: 100 shares on 1 Jan 1999
After 1999 split (2:1): 200 shares
After 2004 split (2:1): 400 shares
After 2014 bonus (1:1): 800 shares
After 2018 bonus (1:1): 1600 shares

Final expected quantity: 1600 shares
Expected total_invested: unchanged from original investment
```

Verify expected final quantity against public NSE records before hardcoding in test.

### TCS (TCS.NS)

| Event | Date | Detail |
|---|---|---|
| Split | Jul 2014 | 1:5 split (1 share became 5) |

**Integration test scenario — TCS:**
```
Buy: 10 shares on 1 Jan 2010
After 2014 split (1:5): 50 shares

Final expected quantity: 50 shares
```

---

## Coverage Requirements

Run coverage with:
```bash
make test-cov
```

Or:
```bash
poetry run pytest tests/ --cov=app --cov-report=term-missing
```

**Minimum coverage thresholds — enforced by PM agent:**

| Module | Required Coverage |
|---|---|
| `app/corporate_actions/` | 95% |
| `app/reconstruction/` | 95% |
| `app/wealth_engine/` | 90% |
| `app/pipeline/normalization/` | 85% |
| `app/explainability/` | 80% |
| `app/api/` | 75% |
| Overall project | 85% |

A PR that drops any module below its threshold is blocked by the PM agent.

---

## Async Test Configuration

All async tests require the `pytest-asyncio` marker. Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

With `asyncio_mode = "auto"`, all async test functions are automatically treated as async without needing `@pytest.mark.asyncio` on every function.

---

## conftest.py — Required Fixtures

```python
# tests/conftest.py
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.models.base import Base

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def base_portfolio_state():
    return PortfolioState(
        date=date(2000, 1, 1),
        quantity=Decimal("100"),
        cost_basis_per_share=Decimal("500.00"),
        total_invested=Decimal("50000.00"),
        cumulative_dividends_received=Decimal("0.00")
    )

@pytest.fixture
def split_action_2_to_1():
    return {
        "action_date": date(2004, 6, 1),
        "action_type": "SPLIT",
        "numerator": Decimal("2"),
        "denominator": Decimal("1")
    }
```

---

## What the PM Agent Checks in Tests

At each phase gate, the PM agent reads pytest output and verifies:

1. Zero failures in `tests/unit/corporate_actions/`
2. Zero failures in `tests/unit/reconstruction/`
3. Coverage thresholds met per module
4. No test uses random or non-deterministic values for financial assertions
5. Every new corporate action handler has a corresponding test file
6. Integration tests use real historical tickers with verified expected quantities

Any of these failing results in a BLOCK — the developer agent cannot proceed to the next phase.
