# PROJECT_OVERVIEW.md
# Passive Wealth Reconstruction Engine

---

## What This Product Is

A backend-focused financial analytics engine that reconstructs long-term shareholder wealth for Indian equity investors using historical market data and chronological corporate actions.

The system takes a simple input — a stock ticker, a buy date, a quantity, and a buy price — and produces a complete, mathematically correct, human-readable breakdown of exactly how that investment evolved over time.

---

## The Problem It Solves

Long-term Indian equity investors cannot easily calculate their true wealth position after years of corporate actions. A person who bought 100 shares of Infosys in 2000 has no simple way to determine:

- How many shares they actually own today after splits and bonuses
- How much dividend income they have received over 24 years
- What their true cost basis is after quantity adjustments
- What their unrealized gain actually is versus what passive income they have already received

Current solutions require manual spreadsheet work, are mathematically confusing after multiple corporate actions, and produce error-prone results.

---

## What This Product Does

The engine automates the entire reconstruction process:

1. Accepts a buy position as input
2. Fetches historical market data and corporate actions from Yahoo Finance and NSE
3. Replays every corporate action chronologically in the correct sequence
4. Reconstructs the exact share quantity at every point in time
5. Calculates total dividends received with correct ex-date eligibility
6. Separates realized income from unrealized appreciation
7. Returns a fully explainable, event-by-event wealth timeline

---

## What This Product Does NOT Do

The following are explicitly out of scope for V1 and must not be built:

- User authentication or accounts of any kind
- Storage of user inputs or calculation results
- Intraday trading analysis
- Portfolio prediction or forecasting
- Buyback processing
- Rights issue processing
- Multi-stock portfolio aggregation
- Deployment infrastructure
- Cross-holding or conglomerate analysis
- Any frontend beyond what FastAPI provides at /docs

---

## V1 Supported Corporate Actions

- Stock splits
- Bonus issues
- Cash dividends

Everything else is a V2 concern.

---

## Target User

For demonstration and proof-of-concept purposes, this is a single-user local application. There are no user accounts, no multi-tenancy, and no data persistence between sessions beyond the market data and corporate actions stored in the local PostgreSQL database.

---

## Core Design Philosophy

The product is built on three non-negotiable principles:

**Correctness over speed.** Every financial calculation must be mathematically exact. A fast wrong answer is worse than a slow correct one.

**Explainability over metrics.** The product does not show percentage returns. It shows exactly what happened, when it happened, and why the number changed.

**Transparency over complexity.** Every rupee in the output must be traceable to a specific event in the timeline. Black-box aggregations are not acceptable.

---

## How to Read This Project

Start with this document. Then read in this order:
1. FINANCIAL_CONCEPTS.md — understand the domain before touching any code
2. ARCHITECTURE.md — understand the system before writing any module
3. DEVELOPMENT_SEQUENCE.md — understand the build order before writing any file
