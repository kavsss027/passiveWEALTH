# DATABASE_SCHEMA.md
# Database Schema — Tables, Columns, Types, and Design Decisions

---

## Design Principles

1. All monetary values stored as NUMERIC(20, 4) — never FLOAT
2. All share quantities stored as NUMERIC(20, 4) — never INTEGER or FLOAT
3. All tables include created_at and updated_at timestamps
4. Soft deletes on all tables — deleted_at TIMESTAMP NULL, never hard delete financial records
5. All date fields for financial events stored as DATE, not TIMESTAMP, unless time precision is required
6. All text identifiers (tickers, action types) stored as VARCHAR with explicit length limits

---

## Table: raw_market_data

Stores historical OHLC price data per ticker per date as fetched from Yahoo Finance.

```sql
CREATE TABLE raw_market_data (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(20)     NOT NULL,
    exchange        VARCHAR(10)     NOT NULL,       -- NSE or BSE
    trade_date      DATE            NOT NULL,
    open_price      NUMERIC(20, 4)  NOT NULL,
    high_price      NUMERIC(20, 4)  NOT NULL,
    low_price       NUMERIC(20, 4)  NOT NULL,
    close_price     NUMERIC(20, 4)  NOT NULL,
    volume          BIGINT          NOT NULL,
    data_source     VARCHAR(50)     NOT NULL,       -- yahoo_finance
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP       NULL,

    CONSTRAINT uq_market_data_ticker_date UNIQUE (ticker, exchange, trade_date)
);

CREATE INDEX idx_market_data_ticker_date ON raw_market_data (ticker, trade_date);
```

---

## Table: raw_dividends

Stores dividend records per ticker as fetched from Yahoo Finance.

```sql
CREATE TABLE raw_dividends (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(20)     NOT NULL,
    exchange        VARCHAR(10)     NOT NULL,
    ex_date         DATE            NOT NULL,       -- eligibility cutoff date
    dividend_amount NUMERIC(20, 4)  NOT NULL,       -- amount per share in INR
    data_source     VARCHAR(50)     NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP       NULL,

    CONSTRAINT uq_dividends_ticker_exdate UNIQUE (ticker, exchange, ex_date)
);

CREATE INDEX idx_dividends_ticker_exdate ON raw_dividends (ticker, ex_date);
```

---

## Table: raw_corporate_actions

Stores raw corporate action records before classification. Populated from NSE and Yahoo Finance. Both sources write here, then the normalization layer resolves conflicts.

```sql
CREATE TABLE raw_corporate_actions (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(20)     NOT NULL,
    exchange        VARCHAR(10)     NOT NULL,
    action_date     DATE            NOT NULL,       -- ex-date for the action
    action_type_raw VARCHAR(100)    NOT NULL,       -- raw string from source
    numerator       NUMERIC(20, 4)  NOT NULL,       -- ratio numerator
    denominator     NUMERIC(20, 4)  NOT NULL,       -- ratio denominator
    data_source     VARCHAR(50)     NOT NULL,       -- yahoo_finance, nse, bse
    raw_payload     JSONB           NULL,           -- original response stored for debugging
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP       NULL
);

CREATE INDEX idx_raw_actions_ticker_date ON raw_corporate_actions (ticker, action_date);
```

---

## Table: corporate_actions

Normalized and classified corporate actions. This is the table the reconstruction engine reads from. Written by the normalization layer after resolving raw_corporate_actions.

```sql
CREATE TABLE corporate_actions (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(20)     NOT NULL,
    exchange        VARCHAR(10)     NOT NULL,
    action_date     DATE            NOT NULL,
    action_type     VARCHAR(20)     NOT NULL,       -- SPLIT, BONUS, DIVIDEND
    numerator       NUMERIC(20, 4)  NOT NULL,
    denominator     NUMERIC(20, 4)  NOT NULL,
    notes           TEXT            NULL,
    data_source     VARCHAR(50)     NOT NULL,
    confidence      VARCHAR(20)     NOT NULL,       -- HIGH, MEDIUM, LOW
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP       NULL,

    CONSTRAINT uq_corporate_actions UNIQUE (ticker, exchange, action_date, action_type),
    CONSTRAINT chk_action_type CHECK (action_type IN ('SPLIT', 'BONUS', 'DIVIDEND'))
);

CREATE INDEX idx_corporate_actions_ticker_date ON corporate_actions (ticker, action_date);
```

**confidence field values:**
- HIGH — NSE and Yahoo Finance agree on type, date, and ratio
- MEDIUM — One source confirmed, other not available
- LOW — Sources disagree, manual review recommended, engine still processes but flags in output

---

## Column Type Decisions

**Why NUMERIC(20, 4) not FLOAT:**
Float stores binary approximations. 2.50 stored as float may retrieve as 2.4999999. When multiplied across 400 shares across 15 dividend events, the rounding error compounds into incorrect rupee values. NUMERIC is arbitrary precision — 2.50 stores and retrieves as exactly 2.50.

**Why NUMERIC for quantity not INTEGER:**
Intermediate calculations during chronological replay can produce fractional quantities temporarily. Storing as NUMERIC preserves precision through the calculation chain. Final output rounds to integer for display.

**Why DATE not TIMESTAMP for financial dates:**
Ex-dates, action dates, and trade dates are calendar-day concepts in Indian equity markets. Time of day is irrelevant and storing timestamps introduces timezone handling complexity with no benefit.

**Why JSONB for raw_payload:**
The original API response from external sources is stored in full for debugging. If a calculation produces a suspicious result, the developer can inspect exactly what data was received from the source.

---

## Alembic Migration Rules

1. Every schema change gets its own migration file
2. Migration file names must be descriptive: `add_confidence_to_corporate_actions` not `update_table`
3. Every migration must include both upgrade() and downgrade() functions
4. Never edit an existing migration file after it has been applied to any environment
5. Run `alembic upgrade head` before starting the application on a fresh database
