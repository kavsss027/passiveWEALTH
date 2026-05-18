# API_CONTRACTS.md
# API Contracts — Endpoints, Request Shapes, Response Shapes

---

## Base URL

```
http://localhost:8000/api/v1
```

Interactive documentation available at:
```
http://localhost:8000/docs
```

---

## Endpoint 1 — Reconstruct Portfolio

**POST /api/v1/portfolio/reconstruct**

The primary endpoint. Accepts a buy position and returns the complete wealth reconstruction timeline.

### Request Body

```json
{
    "ticker": "INFY",
    "exchange": "NSE",
    "buy_date": "2000-01-15",
    "quantity": 100,
    "total_amount_invested": 50000.00
}
```

**Field rules:**
- `ticker` — uppercase, no exchange suffix. Engine appends .NS or .BO internally.
- `exchange` — must be "NSE" or "BSE"
- `buy_date` — ISO 8601 format YYYY-MM-DD. Must not be in the future. Must not be before 1990-01-01.
- `quantity` — positive integer. Minimum 1.
- `total_amount_invested` — optional positive decimal. The total amount paid for the position. If omitted, buy price is auto-fetched from historical closing price on `buy_date`.


### Response Body — Success (200)

```json
{
    "ticker": "INFY",
    "exchange": "NSE",
    "buy_date": "2000-01-15",
    "original_quantity": 100,
    "original_investment": "50000.0000",

    "current_state": {
        "quantity": 1600,
        "current_price_per_share": "1820.50",
        "current_market_value": "2912800.0000",
        "adjusted_cost_basis_per_share": "31.2500",
        "total_invested": "50000.0000"
    },

    "wealth_summary": {
        "total_dividends_received": "48250.0000",
        "unrealized_gain": "2862800.0000",
        "unrealized_gain_label": "if sold at current market price",
        "total_wealth_if_sold": "2961050.0000",
        "wealth_multiple": "59.22"
    },

    "timeline": [
        {
            "event_date": "2000-01-15",
            "event_type": "BUY",
            "description": "Purchased 100 shares of INFY at ₹500.00 per share",
            "quantity_before": 0,
            "quantity_after": 100,
            "financial_impact": "50000.0000",
            "impact_type": "INVESTED",
            "cumulative_dividends": "0.0000"
        },
        {
            "event_date": "2004-06-01",
            "event_type": "SPLIT",
            "description": "Stock split 2:1. Holdings doubled from 100 to 200 shares. Cost basis adjusted from ₹500.00 to ₹250.00 per share.",
            "quantity_before": 100,
            "quantity_after": 200,
            "financial_impact": "0.0000",
            "impact_type": "STRUCTURAL",
            "cumulative_dividends": "0.0000"
        },
        {
            "event_date": "2006-07-14",
            "event_type": "DIVIDEND",
            "description": "Dividend of ₹7.50 per share received on 200 shares. ₹1,500.00 credited.",
            "quantity_before": 200,
            "quantity_after": 200,
            "financial_impact": "1500.0000",
            "impact_type": "REALIZED",
            "cumulative_dividends": "1500.0000"
        },
        {
            "event_date": "2018-06-01",
            "event_type": "BONUS",
            "description": "Bonus issue 1:1. 800 additional shares issued. Holdings increased from 800 to 1600 shares.",
            "quantity_before": 800,
            "quantity_after": 1600,
            "financial_impact": "0.0000",
            "impact_type": "STRUCTURAL",
            "cumulative_dividends": "48250.0000"
        }
    ],

    "data_quality": {
        "confidence": "HIGH",
        "sources_used": ["yahoo_finance", "nse"],
        "warnings": []
    }
}
```

**Key response rules:**
- All monetary values returned as strings to preserve Decimal precision. Client must treat as numeric.
- `unrealized_gain_label` is always present and always reads "if sold at current market price"
- `impact_type` is one of: INVESTED, STRUCTURAL, REALIZED, UNREALIZED
- `timeline` is sorted chronologically ascending, always includes the original BUY event as first item
- `data_quality.confidence` reflects the lowest confidence corporate action in the dataset

---

## Endpoint 2 — Fetch Corporate Actions

**GET /api/v1/corporate-actions/{ticker}**

Returns all corporate actions on record for a ticker. Used for inspection and debugging.

### Path Parameters
- `ticker` — uppercase ticker symbol, no exchange suffix

### Query Parameters
- `exchange` — NSE or BSE, default NSE
- `from_date` — ISO 8601, optional, filters actions from this date
- `to_date` — ISO 8601, optional, filters actions to this date

### Response Body — Success (200)

```json
{
    "ticker": "INFY",
    "exchange": "NSE",
    "total_count": 12,
    "actions": [
        {
            "action_date": "2004-06-01",
            "action_type": "SPLIT",
            "numerator": 2,
            "denominator": 1,
            "data_source": "nse",
            "confidence": "HIGH"
        }
    ]
}
```

---

## Endpoint 3 — Fetch Market Data

**GET /api/v1/market-data/{ticker}**

Returns historical OHLC data for a ticker. Used for inspection.

### Path Parameters
- `ticker` — uppercase ticker symbol

### Query Parameters
- `exchange` — NSE or BSE, default NSE
- `from_date` — ISO 8601, required
- `to_date` — ISO 8601, required

### Response Body — Success (200)

```json
{
    "ticker": "INFY",
    "exchange": "NSE",
    "from_date": "2000-01-01",
    "to_date": "2000-12-31",
    "data_points": 247,
    "prices": [
        {
            "trade_date": "2000-01-17",
            "open": "485.00",
            "high": "512.00",
            "low": "480.00",
            "close": "500.00",
            "volume": 1250000
        }
    ]
}
```

---

## Error Responses

All errors follow this shape:

```json
{
    "error": {
        "code": "INVALID_BUY_DATE",
        "message": "buy_date 2026-01-01 is in the future",
        "field": "buy_date"
    }
}
```

**Error codes:**

| Code | HTTP Status | Meaning |
|---|---|---|
| INVALID_TICKER | 422 | Ticker not found or no data available |
| INVALID_BUY_DATE | 422 | Date is in future or before 1990 |
| INVALID_QUANTITY | 422 | Quantity is zero or negative |
| INVALID_EXCHANGE | 422 | Exchange not NSE or BSE |
| DATA_FETCH_FAILED | 503 | External data source unreachable |
| RECONSTRUCTION_FAILED | 500 | Engine error during calculation |
| NO_DATA_AVAILABLE | 404 | No market data found for ticker in date range |

---

## API Versioning Rule

All endpoints are prefixed with `/api/v1/`. When V2 is introduced, V1 endpoints remain unchanged. Never modify a V1 endpoint's response shape after the first release.
