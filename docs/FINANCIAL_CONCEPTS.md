# FINANCIAL_CONCEPTS.md
# Financial Domain Knowledge — Required Reading Before Writing Any Code

---

## Why This Document Exists

This project handles real financial calculations. A developer who misunderstands the domain will write code that compiles, passes naive tests, and produces wrong rupee values. Read this document completely before writing a single line of business logic.

---

## 1. Corporate Actions — What They Are

A corporate action is any event initiated by a company that materially affects its shares or shareholders. This project handles three types.

---

## 2. Stock Splits

A stock split increases the number of shares outstanding by dividing each existing share into multiple shares.

**Example:** A 2:1 split means every 1 share becomes 2 shares. The total value of the holding does not change on the split date. Only the quantity and price per share change.

**Mathematical rule:**
```
new_quantity = old_quantity * split_numerator / split_denominator
new_price_per_share = old_price * split_denominator / split_numerator
cost_basis_per_share = original_cost_basis * split_denominator / split_numerator
```

**Real example:**
- Holding: 100 shares at ₹500 each, total value ₹50,000
- 2:1 split occurs
- After: 200 shares at ₹250 each, total value ₹50,000
- Cost basis per share adjusts from ₹500 to ₹250

**Critical:** A split does not create profit. It does not generate cash. It is a structural change to ownership. Never classify a split event as income.

---

## 3. Bonus Issues

A bonus issue is when a company issues additional free shares to existing shareholders from its accumulated reserves.

**Example:** A 1:1 bonus means for every 1 share held, the shareholder receives 1 additional share free.

**Mathematical rule:**
```
new_quantity = old_quantity + (old_quantity * bonus_numerator / bonus_denominator)
```

**Real example:**
- Holding: 100 shares
- 1:1 bonus issued
- After: 200 shares

**How bonus differs from split:**
- A split restructures existing shares. A bonus creates new shares from company reserves.
- For quantity calculation in this engine, the effect on holdings is similar — both increase share count.
- The critical difference is financial meaning for explainability: a bonus is a reward from retained earnings, a split is a structural restructuring. The narrative engine must use different language for each.
- Yahoo Finance treats both as splits in their data. The NSE data source is used to correctly classify which events are bonus and which are splits. This is a known data source limitation that the ingestion layer resolves.

**Critical:** Like splits, bonus issues do not create direct cash profit. Do not classify bonus events as income.

---

## 4. Cash Dividends

A dividend is a cash payment made by the company to its shareholders from profits.

**Mathematical rule:**
```
dividend_received = quantity_on_ex_date * dividend_per_share
```

**Critical concept — the ex-dividend date:**
The ex-dividend date is the cutoff date that determines dividend eligibility.

Rule: A shareholder must have purchased the stock BEFORE the ex-dividend date to receive the dividend.

```
eligible = buy_date < ex_dividend_date
```

If buy_date equals ex_dividend_date, the investor is NOT eligible. The condition is strictly less than.

**Why this matters for reconstruction:** The quantity used for dividend calculation is the quantity the investor held on the ex-dividend date — not the current quantity and not the original quantity. If splits or bonuses occurred between the buy date and the ex-date, the quantity on ex-date must reflect those adjustments.

**Dividends are realized income.** Dividend income is cash already received by the investor. It is unconditional. Always classify dividends as realized.

---

## 5. Realized vs Unrealized Wealth — The Most Important Distinction

**Realized income:**
Cash that has already been received by the investor. It is unconditional and permanent. In this system, dividends are the only source of realized income.

```
total_realized = sum of all dividends received across all ex-dates
```

**Unrealized gains:**
The paper profit from market appreciation. This money does not exist until the investor sells. It is conditional on the current market price.

```
unrealized_gain = (current_market_price - adjusted_cost_basis) * current_quantity
```

This must always be labeled in outputs as: "if sold at current market price"

Never present unrealized gains as profit the investor has made. They have not made it. They will make it only if and when they sell.

**Structural events:**
Splits and bonuses are neither realized nor unrealized gains. They are structural. They change quantity and cost basis but create no wealth by themselves.

```
wealth_change_from_split = 0
wealth_change_from_bonus = 0
```

---

## 6. Chronological Event Sequencing — Order Is Everything

Corporate actions must be processed in strict chronological order. The order in which events are applied changes the mathematical outcome.

**Example showing why order matters:**

Scenario: 100 shares bought. Two events occur: a 2:1 split on June 1, and a dividend of ₹5/share with ex-date June 15.

Correct order (split first, then dividend):
```
After split: 200 shares
Dividend received: 200 * ₹5 = ₹1,000
```

Wrong order (dividend first, then split):
```
Dividend received: 100 * ₹5 = ₹500  ← WRONG
After split: 200 shares
```

The difference is ₹500. This is a financially incorrect calculation produced by wrong sequencing. The engine must sort all corporate actions by date in ascending order before processing begins. This is non-negotiable.

---

## 7. Adjusted Cost Basis

The cost basis is the original price paid per share. It must be adjusted every time a split or bonus occurs, because the number of shares changes but the total invested amount does not.

```
adjusted_cost_basis = total_amount_invested / current_quantity
```

Track total amount invested as a fixed value. Recalculate cost basis per share whenever quantity changes.

**Example:**
- Bought 100 shares at ₹500. Total invested: ₹50,000. Cost basis: ₹500/share.
- 2:1 split. Now 200 shares. Total invested still ₹50,000. Cost basis: ₹250/share.
- 1:1 bonus. Now 400 shares. Total invested still ₹50,000. Cost basis: ₹125/share.

The total invested amount never changes because of structural events. Only the per-share cost basis changes.

---

## 8. Edge Cases the Engine Must Handle

**Two corporate actions on the same date:**
Process in this priority order: split first, then bonus, then dividend. Document this rule in code.

**Buy date equals ex-dividend date:**
Investor is NOT eligible. Condition is strictly less than.

**Corporate action before buy date:**
Ignore it. It has no effect on this investor's holdings.

**Fractional shares from intermediate calculations:**
Indian exchanges do not permit fractional shares in final holdings. However, intermediate calculations may produce fractions due to ratio arithmetic. Use Decimal arithmetic throughout. Round to integer only at the final output step.

---

## 9. Ticker Symbol Format for Indian Stocks

Yahoo Finance requires specific suffixes for Indian exchange stocks:

```
NSE listed stocks: TICKER.NS   (example: INFY.NS, TCS.NS, RELIANCE.NS)
BSE listed stocks: TICKER.BO   (example: INFY.BO, TCS.BO)
```

Always use the .NS suffix as primary. Fall back to .BO if .NS is unavailable.
