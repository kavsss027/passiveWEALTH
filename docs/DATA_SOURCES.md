# DATA_SOURCES.md
# Data Sources — What Each Source Provides, How to Access It, Known Limitations

---

## Source Hierarchy

```
Primary OHLC + Dividends:  Yahoo Finance (yfinance)
Primary Action Type:        NSE India (scraped)
Cross-validation:           BSE India (scraped, light use)
Conflict resolution:        NSE wins over Yahoo on action type classification
```

---

## Source 1 — Yahoo Finance via yfinance

### What It Provides

| Data | Available | Quality |
|---|---|---|
| Historical OHLC prices | Yes | Good |
| Dividend history with ex-dates | Yes | Good, some gaps pre-2000 |
| Split and bonus ratios | Yes | Good ratios, wrong type labels |
| Bonus vs split classification | No | Yahoo treats both as splits |

### How to Use It

```python
import yfinance as yf

# Always use .NS suffix for NSE stocks
ticker = yf.Ticker("INFY.NS")

# Historical OHLC — auto-adjusts prices for splits by default
# Use auto_adjust=False to get raw unadjusted prices
hist = ticker.history(start="2000-01-01", end="2024-01-01", auto_adjust=False)

# Dividend history
dividends = ticker.dividends

# Split and bonus history (ratio only, no type classification)
splits = ticker.splits
```

**Important — auto_adjust parameter:**
Yahoo returns split-adjusted prices by default. For this engine, fetch with `auto_adjust=False` to get raw prices, then apply adjustments manually through the reconstruction engine. This ensures our calculations are transparent and auditable.

### Known Limitations

**The bonus/split distinction problem:**
When Yahoo Finance records a 1:1 bonus issue, it appears in `ticker.splits` as ratio `2.0` — identical to how a 2:1 stock split appears. There is no field distinguishing them.

This is resolved by cross-referencing NSE data. The NSE corporate actions endpoint explicitly labels each event as BONUS or SPLIT.

**Rate limits:**
Approximately 2,000 requests per hour per IP. Since this is a local application hitting Yahoo on an as-needed basis, this limit is unlikely to be reached. If it is, the error response is an HTTP 429 or a connection error from yfinance. Handle this with a retry after 60 seconds.

**Data availability:**
Reliable from approximately 1995 onwards for major NSE stocks. Pre-1995 data is sparse or unavailable.

---

## Source 2 — NSE India (Primary for Action Classification)

### What It Provides

NSE's corporate actions data explicitly classifies each event as BONUS, SPLIT, DIVIDEND, RIGHTS, or BUYBACK. This is the authoritative source for determining whether a quantity-change event is a bonus or a split.

### Endpoint

```
https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={TICKER}
```

Example:
```
https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=INFY
```

Note: ticker symbol for NSE has no exchange suffix — just the raw ticker.

### Session Requirement — Critical

NSE blocks requests that do not come from an established browser session. A direct GET request to the API endpoint returns 401 or an empty response.

**Required session establishment sequence:**

```python
import httpx

async def get_nse_session() -> httpx.AsyncClient:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    client = httpx.AsyncClient(headers=headers, follow_redirects=True)

    # Step 1: Hit homepage to establish session cookie
    await client.get("https://www.nseindia.com")

    # Step 2: Hit the main equities page — some NSE endpoints require this
    await client.get("https://www.nseindia.com/market-data/live-equity-market")

    # Client now has valid session cookies — return it for subsequent API calls
    return client
```

**After session establishment:**
```python
async with await get_nse_session() as client:
    response = await client.get(
        f"https://www.nseindia.com/api/corporates-corporateActions",
        params={"index": "equities", "symbol": ticker}
    )
    data = response.json()
```

### Response Structure from NSE

```json
[
    {
        "symbol": "INFY",
        "series": "EQ",
        "faceVal": "5.00",
        "purpose": "BONUS",
        "exDate": "18-JUN-2018",
        "recDate": "19-JUN-2018",
        "bcStartDate": "-",
        "bcEndDate": "-",
        "ndStartDate": "-",
        "ndEndDate": "-",
        "paymentDate": "-",
        "caBroadcastDate": "05-JUN-2018",
        "comp": "Infosys Limited"
    }
]
```

**Key fields:**
- `purpose` — the action type classification. Values include: BONUS, SPLIT, DIVIDEND, RIGHTS, BUY-BACK
- `exDate` — the ex-date in DD-MMM-YYYY format. Must be parsed and converted to YYYY-MM-DD.
- `faceVal` — face value, useful for cross-validating split ratios

**Date parsing:**
```python
from datetime import datetime
ex_date = datetime.strptime(action["exDate"], "%d-%b-%Y").date()
```

### NSE Data Limitations

NSE API returns approximately 2-3 years of recent corporate action history by default. For older historical actions, BSE data or Yahoo Finance data must be used, with manual type classification where possible.

---

## Source 3 — BSE India (Cross-Validation Only)

BSE is used to cross-validate NSE data when the NSE response looks inconsistent, or when NSE data is unavailable for a specific ticker.

### Endpoint

```
https://api.bseindia.com/BseIndiaAPI/api/CorporateAction/w?scripcode={BSE_CODE}&type=CA
```

BSE uses numeric scrip codes, not ticker symbols. Requires a ticker-to-scrip-code mapping table.

### Usage Rule

BSE is never the primary source. Only call BSE when:
1. NSE returns empty data for a ticker
2. NSE and Yahoo Finance disagree on a ratio and BSE can serve as tiebreaker

---

## Conflict Resolution Rules

When two sources provide different information for the same corporate action:

```
Action type (BONUS vs SPLIT):
    NSE label wins always.

Action date:
    NSE date wins. If NSE has no record, Yahoo date is used.

Ratio:
    If NSE and Yahoo agree → HIGH confidence.
    If only one source has data → MEDIUM confidence.
    If NSE and Yahoo disagree by more than 0.01 → LOW confidence, log warning, use NSE value.

Dividend amount:
    Yahoo Finance amount is used as primary.
    If BSE provides a different amount → flag as LOW confidence, log both values.
```

---

## Data Freshness Rules

Market data and corporate actions are fetched from external sources and stored in PostgreSQL. They are not re-fetched on every request.

```
Market data (OHLC):     Fetch if not present for the requested date range
Dividends:              Fetch if not present for the requested ticker
Corporate actions:      Fetch if not present for the requested ticker
```

Since this is a local single-user application, there is no scheduled refresh. Data for a ticker is fetched once and reused. If a user wants fresh data for a ticker, they can clear the relevant database records and re-request.

---

## Error Handling for External Sources

All external HTTP calls are wrapped in try/except. If Yahoo Finance or NSE is unreachable:

1. Check PostgreSQL for existing data
2. If existing data covers the requested date range, use it and add a warning to `data_quality.warnings` in the response
3. If no existing data and external source unreachable, raise `DataFetchFailedError` which returns HTTP 503

---

## Historical Data Override Policy

### Why Overrides Exist
Due to severe limitations in raw data quality from live external sources (Yahoo Finance and NSE) for pre-2008 corporate action history in India, certain actions cannot be dynamically ingested and classified correctly:
1. **Yahoo Finance Gaps:** Yahoo Finance frequently has completely missing splits or misclassifies structural 1:1 bonus issues as stock splits (using raw `2.0` multipliers) without distinguishing the type.
2. **NSE History Gaps:** The NSE API does not return structural actions (splits/bonuses) prior to ~2005-2008, or returns them with unparseable ratios in the text fields.

To maintain 100% mathematical correctness for long-term integration cases (e.g. INFY 100 → 1600 shares, TCS 10 → 50 shares), we implement **authoritative overrides** for splits and bonuses.

### What is the Override File
The override configurations are stored in JSON format inside the backend core module:
- **File path:** [historical_overrides.json](file:///d:/passiveWEALTH/backend/app/core/historical_overrides.json)

The file maps uppercase ticker symbols to a list of authoritative structural corporate actions. Example:
```json
{
  "TCS": [
    {
      "action_date": "2014-05-23",
      "action_type": "SPLIT",
      "numerator": 5.0,
      "denominator": 1.0,
      "notes": "Authoritative split 5:1"
    }
  ]
}
```

### How it is Integrated in the Pipeline
During the reconstruction request inside [reconstruction_service.py](file:///d:/passiveWEALTH/backend/app/services/reconstruction_service.py):
1. **Dynamic Fetching & Ingestion:** The service first fetches all raw history from live APIs (Yahoo Finance and NSE), runs standard normalizers, and persists them.
2. **Culling and Overriding:** If the ticker exists in `historical_overrides.json`, the service deletes any normalized splits/bonuses for that ticker and replaces them with the high-confidence overrides from the JSON file.
3. **Dividends Remaining Dynamic:** All cash dividend actions continue to load dynamically from Yahoo Finance/NSE on every run.

### How to Add a New Ticker Override
To add a new ticker's verified pre-2008 split/bonus history:
1. Open the [historical_overrides.json](file:///d:/passiveWEALTH/backend/app/core/historical_overrides.json) file.
2. Add a new key for the uppercase ticker (e.g., `"WIPRO"`).
3. Under the key, add a JSON list of objects containing `action_date` (YYYY-MM-DD), `action_type` (`"SPLIT"` or `"BONUS"`), `numerator` (float), `denominator` (float), and `notes`.
4. Trigger your next reconstruction request. The pipeline will automatically apply the overrides post-normalization.

