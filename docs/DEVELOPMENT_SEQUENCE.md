# DEVELOPMENT_SEQUENCE.md
# Development Sequence — Build Order, Dependencies, and Phase Gates

---

## The Most Important Rule

No phase begins until the previous phase has a passing test suite.

The PM agent enforces this. Do not attempt to start Phase 2 if Phase 1 tests are failing. Do not attempt to start Phase 4 if Phase 3 tests are failing. The gate is hard.

---

## Why Sequence Matters for This Project

This project has hard dependency chains. Examples:

- `dividend.py` cannot be correctly implemented without `quantity_tracker.py` — dividends need the quantity on ex-date, which the tracker maintains
- `reconstruction/engine.py` cannot be built until all three action handlers exist — the engine calls each handler
- The API layer cannot be built until services exist — services wrap the engines
- Services cannot be built until engines exist — engines perform the calculations

Build in the wrong order and you write code against wrong assumptions that survive into production.

---

## Phase 0 — Project Scaffolding

**Goal:** Empty project structure exists. Docker is running. App starts without errors.

**What to build:**
```
passive-wealth-engine/
├── backend/
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── Makefile
│   ├── Dockerfile
│   ├── .env.example
│   ├── .python-version          (contains: 3.11)
│   ├── alembic.ini
│   ├── migrations/
│   │   └── versions/            (empty)
│   └── app/
│       ├── __init__.py
│       └── main.py              (FastAPI app with /health endpoint only)
├── docker-compose.yml
└── .agents/rules/               (all 16 docs — already done)
```

**Gate condition:**
```bash
docker-compose up -d db          # PostgreSQL starts
poetry run uvicorn app.main:app  # FastAPI starts, no errors
curl localhost:8000/health       # returns {"status": "ok"}
```

PM agent check: app starts, health endpoint responds, no import errors.

---

## Phase 1 — Foundation

**Goal:** Core config, exceptions, database models, and schemas are in place. Migrations run cleanly.

**Build order within this phase — strict:**

```
1. app/core/config.py            pydantic-settings config class
2. app/core/exceptions.py        all typed exceptions for the project
3. app/core/constants.py         action type strings, exchange codes
4. app/core/logging.py           structlog configuration
5. app/database/connection.py    async SQLAlchemy engine + session factory
6. app/database/models/base.py   declarative base with timestamps
7. app/database/models/market_data.py
8. app/database/models/corporate_actions.py
9. app/database/models/raw_corporate_actions.py
10. app/database/models/raw_dividends.py
11. migrations/                  Alembic migration for all tables
12. app/schemas/portfolio.py     Pydantic request/response schemas
13. app/schemas/wealth.py
14. app/schemas/timeline.py
15. app/schemas/corporate_actions.py
16. app/utils/date_utils.py
17. app/utils/financial_math.py
18. app/utils/validators.py
```

**Do not build repositories yet.** Repositories come in Phase 2 when they have something meaningful to query.

**Gate conditions — all must pass:**
```bash
make migrate                     # all migrations apply cleanly
make test                        # Phase 1 tests pass
```

Phase 1 tests must cover:
- config loads and validates all required env vars
- all typed exceptions can be raised and caught
- database models can be created and queried (basic CRUD per model)
- Pydantic schemas validate correct inputs
- Pydantic schemas reject invalid inputs with correct error codes
- date_utils functions return correct results
- financial_math Decimal operations produce exact expected values

PM agent check: all Phase 1 tests pass, no float used in models or schemas, NUMERIC(20,4) used for all monetary columns.

---

## Phase 2 — Data Pipeline

**Goal:** Market data and corporate actions can be fetched from external sources and stored in PostgreSQL.

**Build order within this phase — strict:**

```
1. app/database/repositories/base_repo.py      abstract base repository
2. app/database/repositories/market_data_repo.py
3. app/database/repositories/corporate_actions_repo.py
4. app/database/repositories/raw_dividends_repo.py
5. app/pipeline/ingestion/yahoo_finance.py     OHLC + dividends + splits
6. app/pipeline/ingestion/nse.py               corporate action classification
7. app/pipeline/ingestion/bse.py               cross-validation only
8. app/pipeline/normalization/price_normalizer.py
9. app/pipeline/normalization/dividend_normalizer.py
10. app/pipeline/normalization/action_normalizer.py   resolves bonus vs split conflict
```

**The action_normalizer is the most critical file in this phase.**

It receives records from both Yahoo Finance and NSE, resolves conflicts using the rules in DATA_SOURCES.md, and writes classified corporate_actions records to PostgreSQL with the correct confidence level.

**Gate conditions — all must pass:**
```bash
make test
```

Phase 2 tests must cover:
- Yahoo Finance ingestion returns correctly structured data for INFY.NS
- NSE session establishment succeeds and returns valid cookies
- NSE ingestion correctly classifies BONUS vs SPLIT events
- action_normalizer correctly resolves NSE as winner when types conflict
- action_normalizer writes HIGH confidence when both sources agree
- action_normalizer writes LOW confidence when sources disagree on ratio
- all repositories perform CRUD correctly against test database
- normalization produces Decimal values, not floats

**Important:** Phase 2 tests that call real external APIs (Yahoo, NSE) must be tagged with `@pytest.mark.integration` and run separately from unit tests. Unit tests for ingestion use mocked HTTP responses.

PM agent check: data lands in PostgreSQL correctly, bonus/split classification is correct per DATA_SOURCES.md rules, no float values in persisted records.

---

## Phase 3 — Corporate Action Engine

**Goal:** All three corporate action handlers are implemented and tested. The sequencer correctly orders events.

**Build order within this phase — strict:**

```
1. app/corporate_actions/base.py        abstract handler + PortfolioState + ActionResult
2. app/corporate_actions/split.py       implements base, full calculation
3. tests/unit/corporate_actions/test_split_handler.py    WRITE TESTS NOW
4. app/corporate_actions/bonus.py       implements base, full calculation
5. tests/unit/corporate_actions/test_bonus_handler.py    WRITE TESTS NOW
6. app/corporate_actions/dividend.py    implements base, ex-date eligibility
7. tests/unit/corporate_actions/test_dividend_handler.py WRITE TESTS NOW
8. app/corporate_actions/sequencer.py   sort + filter logic
9. tests/unit/corporate_actions/test_sequencer.py        WRITE TESTS NOW
```

The rule: write tests immediately after each handler, before building the next handler. Never batch the tests to the end of the phase.

**Gate conditions — all must pass:**
```bash
make test
make test-cov   # corporate_actions/ must be at 95%+
```

Phase 3 tests must cover per handler:
- correct output quantity after action applied
- correct cost basis adjustment
- correct total_invested preservation
- eligibility returns False when buy_date equals action_date
- eligibility returns False when buy_date is after action_date
- financial_impact is exactly Decimal("0") for splits and bonuses
- impact_type is "STRUCTURAL" for splits and bonuses
- impact_type is "REALIZED" for dividends
- dividend uses quantity at ex-date, not original quantity

Sequencer tests must cover:
- actions sorted chronologically ascending
- when two actions on same date: split before bonus before dividend
- actions before buy_date are filtered out
- empty action list returns empty sorted list

PM agent check: 95%+ coverage on corporate_actions/, all edge cases from CORPORATE_ACTION_LOGIC.md are covered by named test cases, no float arithmetic anywhere in handlers.

---

## Phase 4 — Reconstruction Engine

**Goal:** The state machine replays a sequence of events and produces a correct final portfolio state.

**Build order within this phase — strict:**

```
1. app/reconstruction/quantity_tracker.py
2. tests/unit/reconstruction/test_quantity_tracker.py    WRITE TESTS NOW
3. app/reconstruction/state_machine.py
4. tests/unit/reconstruction/test_state_machine.py       WRITE TESTS NOW
5. app/reconstruction/engine.py
6. tests/unit/reconstruction/test_engine.py              WRITE TESTS NOW
7. tests/integration/test_full_reconstruction_infy.py    real data end-to-end
8. tests/integration/test_full_reconstruction_tcs.py     real data end-to-end
```

**The integration tests in this phase are critical.**

Use the real historical events from TESTING_GUIDE.md. The INFY integration test must verify that buying 100 shares of INFY on 1 Jan 1999 produces exactly 1600 shares after all splits and bonuses. If this test fails, the reconstruction engine has a bug.

**Gate conditions — all must pass:**
```bash
make test
make test-cov   # reconstruction/ must be at 95%+
```

PM agent check: INFY integration test passes with correct final quantity, TCS integration test passes, state machine never produces negative or zero quantity, event log order matches input action order.

---

## Phase 5 — Wealth Engine and Explainability

**Goal:** Realized and unrealized wealth are correctly calculated. Every event has a human-readable description. The full timeline is assembled.

**Build order within this phase — strict:**

```
1. app/wealth_engine/realized.py        sum all dividend ActionResults
2. app/wealth_engine/unrealized.py      current price - adjusted cost basis
3. app/wealth_engine/aggregator.py      combine realized + unrealized + summary
4. tests/unit/wealth_engine/test_realized.py
5. tests/unit/wealth_engine/test_unrealized.py
6. app/explainability/event_formatter.py    all format_* functions per EXPLAINABILITY_RULES.md
7. app/explainability/narrative_builder.py  assembles timeline list
8. app/timeline/generator.py
9. app/timeline/renderer.py
10. tests/unit/explainability/test_event_formatter.py
```

**Gate conditions — all must pass:**
```bash
make test
make test-cov   # wealth_engine/ must be 90%+, explainability/ must be 80%+
```

Key tests:
- unrealized_gain always includes "if sold at current market price" label
- dividends are never labeled as UNREALIZED or STRUCTURAL
- splits and bonuses are never labeled as REALIZED
- timeline first entry is always the BUY event
- timeline is sorted chronologically ascending
- cumulative_dividends in each timeline entry is a running total

PM agent check: unrealized gain label matches exactly the string in EXPLAINABILITY_RULES.md, no mixing of realized and unrealized without correct labels.

---

## Phase 6 — Service Layer and API

**Goal:** FastAPI endpoints are live. Full end-to-end request returns correct JSON response.

**Build order within this phase — strict:**

```
1. app/services/reconstruction_service.py   orchestrates phases 2-5
2. app/services/wealth_service.py
3. app/services/timeline_service.py
4. app/api/v1/routers/portfolio.py          POST /reconstruct endpoint
5. app/api/v1/routers/corporate_actions.py  GET endpoint
6. app/api/v1/routers/market_data.py        GET endpoint
7. app/api/v1/dependencies.py               DB session injection
8. app/api/middleware/logging.py            request logging
9. tests/integration/test_api_endpoints.py  full HTTP round-trip tests
```

**Gate conditions — final gate:**
```bash
make test                        # full suite passes
make test-cov                    # all thresholds met
curl -X POST localhost:8000/api/v1/portfolio/reconstruct \
  -H "Content-Type: application/json" \
  -d '{"ticker":"INFY","exchange":"NSE","buy_date":"1999-01-01","quantity":100,"buy_price_per_share":500}' \
  | python3 -m json.tool          # returns valid JSON with correct structure
```

PM agent check: response matches API_CONTRACTS.md structure exactly, all error codes from API_CONTRACTS.md are implemented, no business logic inside router files.

---

## Sequence Summary

```
Phase 0    Scaffolding          Docker + FastAPI + /health
Phase 1    Foundation           Core + Models + Schemas + Migrations
Phase 2    Data Pipeline        Ingestion + Normalization + Repositories
Phase 3    Corporate Actions    Split + Bonus + Dividend + Sequencer
Phase 4    Reconstruction       QuantityTracker + StateMachine + Engine
Phase 5    Wealth + Explain     Realized + Unrealized + Timeline
Phase 6    API Layer            Services + Routers + End-to-end
```

Total estimated phases: 6
Each phase blocked until PM agent issues PASS.
