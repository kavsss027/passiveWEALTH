# ARCHITECTURE.md
# System Architecture — Passive Wealth Reconstruction Engine

---

## System Overview

The engine is a stateless request-response system. No user data is persisted. The only data stored in PostgreSQL is public market data and corporate actions fetched from external sources. Every calculation is performed fresh per request.

---

## Data Flow — End to End

```
User Request (ticker + buy_date + quantity + buy_price)
        │
        ▼
FastAPI Router (HTTP layer only — no logic)
        │
        ▼
Service Layer (orchestrates the sequence)
        │
        ├──► Pipeline: Ingestion + Normalization
        │         Checks if data exists in PostgreSQL
        │         Fetches from Yahoo Finance / NSE if not cached
        │         Normalizes and persists to PostgreSQL
        │
        ├──► Corporate Action Sequencer
        │         Fetches all corporate actions for ticker
        │         Sorts chronologically
        │         Filters to actions after buy_date
        │
        ├──► Reconstruction Engine
        │         Replays events using state machine
        │         Tracks quantity at every point in time
        │
        ├──► Wealth Engine
        │         Calculates realized income (dividends)
        │         Calculates unrealized appreciation
        │         Aggregates total wealth picture
        │
        ├──► Explainability Engine
        │         Converts each calculation into narrative text
        │         Applies correct labels (realized / unrealized / structural)
        │
        └──► Timeline Generator
                  Assembles ordered list of wealth events
                  Returns final structured JSON response
```

---

## Architectural Pattern — Event-Based State Machine

The core of this system is a state machine where the portfolio evolves through events.

```
STATE(n+1) = APPLY_EVENT(STATE(n), EVENT(n))
```

A portfolio state is a snapshot of the holding at a point in time:

```python
@dataclass
class PortfolioState:
    date: date
    quantity: Decimal
    cost_basis_per_share: Decimal
    total_invested: Decimal
    cumulative_dividends_received: Decimal
```

An event is a corporate action with a date and parameters. The engine walks through events in chronological order, applying each one to produce the next state.

This design ensures:
- Deterministic results — same inputs always produce same outputs
- Full auditability — every state change has a corresponding event
- Correct sequencing — events cannot be applied out of order

---

## Layer Responsibilities — Strict Boundaries

**Router layer** (`api/v1/routers/`)
- Receives HTTP request
- Validates input schema using Pydantic
- Calls exactly one service method
- Returns HTTP response
- Contains zero business logic

**Service layer** (`app/services/`)
- Orchestrates the sequence of operations
- Calls pipeline, engines, and explainability modules in order
- Handles cross-cutting concerns like error aggregation
- Contains orchestration logic, not calculation logic

**Engine layer** (`corporate_actions/`, `reconstruction/`, `wealth_engine/`, `explainability/`, `timeline/`)
- Contains all financial calculation logic
- Each module is independently testable
- No knowledge of HTTP or database schema
- Operates on domain objects, not database models

**Repository layer** (`database/repositories/`)
- All database interaction lives here
- Services call repositories, never models directly
- Returns domain objects, not SQLAlchemy row objects

**Pipeline layer** (`pipeline/ingestion/`, `pipeline/normalization/`)
- Responsible for fetching and cleaning external data
- Data fetched here lands in PostgreSQL via repositories
- Called by services when data is not already available

---

## Module Dependency Rules

These rules must never be violated:

```
Routers       → may call Services only
Services      → may call Repositories, Engines, Pipeline
Engines       → may call Utils, Core only
               may NOT call Repositories or Services
               may NOT call each other (no engine-to-engine calls)
Repositories  → may call database/models only
Pipeline      → may call Repositories and external APIs only
Utils         → may call Core only
Core          → no dependencies on any internal module
```

If a developer finds themselves importing a repository inside an engine module, that is an architecture violation and must be corrected before the PR is merged.

---

## PostgreSQL — What Is Stored and Why

PostgreSQL stores only public financial data that is expensive to re-fetch. It is a local cache of external data, not a user database.

```
raw_market_data       OHLC prices per ticker per date
raw_dividends         dividend amounts and ex-dates per ticker
raw_splits            split and bonus ratios per ticker per date
corporate_actions     normalized and classified action records
```

No user inputs are stored. No calculation results are stored. No session data is stored.

---

## Stateless Request Design

Every API request is fully self-contained. The sequence per request:

1. Check PostgreSQL for existing market data and corporate actions for the requested ticker
2. If data is missing or stale, fetch from external sources and persist
3. Run the full reconstruction pipeline using inputs from the request
4. Return the result
5. Nothing about this request is remembered after the response is sent

---

## Error Handling Architecture

Errors are handled at the service layer. Engines raise typed exceptions defined in `core/exceptions.py`. Services catch these, log them via structlog, and return appropriate HTTP responses via the router.

Engines must never swallow exceptions silently. Every calculation failure must propagate up with a typed exception that describes exactly what failed and why.

---

## What This Architecture Intentionally Excludes

- No message queues — Celery and Redis removed, not needed for local single-user use
- No background workers — all processing is synchronous per request
- No authentication middleware — no user layer exists
- No rate limiting — single local user, not needed
- No caching layer beyond in-process lru_cache for pure lookups
