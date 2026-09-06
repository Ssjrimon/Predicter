# PREDICTER — COMPLETE PROJECT HANDOFF

Full context transfer. Contains: project origin, complete chronological build history, every bug found and how it was fixed, all verified external facts, build/stack/UI conventions, open items, rejected approaches, and the complete source of every file in the repo.

Everything stated as verified was checked against real uploaded source code, real API responses, or real web sources. Anything unverified is explicitly marked.

**Note on scope (added when this file was committed into the `Ssjrimon/Predicter` repo):** the repository this file lives in also contains an unrelated Android/Kotlin tree (`app/`, `build.gradle.kts`, etc.) from an early, abandoned direction. That tree is **not** the app this handoff describes. The real Predicter app — the one all of the history, bugs, and verified facts below refer to — was built in Google AI Studio (React + TypeScript + Express) and lives only there, not in this repository. The clean-slate rebuild commissioned from this handoff lives in `predicter-v2/` in this repo and does not touch, port from, or inherit any data from either the Kotlin tree or the AI Studio app (different origins — `aistudio.google.com` vs `localhost` — so `localStorage` does not transfer; the archive starts empty).

---

# PART I — PROJECT CONTEXT

## What Predicter is

A personal Kalshi prediction-market analysis tool. React + TypeScript frontend, Express proxy server. Built in Google AI Studio (also touched by Google Antigravity and ChatGPT at points). The user is non-technical and works almost entirely from a phone.

**The user's stated goal:** an adaptive system that finds mispriced Kalshi contracts, proves edge through calibration scoring and backtesting, and eventually auto-trades real money toward financial independence. The current app is the analysis layer. The trading layer does not exist and is gated (see Working Rules).

## Origin — why the discipline exists

The first version, built by Gemini inside AI Studio, failed in specific ways:

- Fabricated sentiment scores presented as real data
- Invented expected-value numbers with no derivation
- No fee math at all
- Crashes caused by using UUIDs as React list keys

Claude rebuilt the domain logic (originally verified Kotlin), then the project moved to a React/TypeScript/Node web app. Claude's role across every session since: **verify every AI-generated change against real code or real screenshots, hand-check all math independently, and catch fabrication.** Every rule below traces back to a real incident.

---

# PART II — NON-NEGOTIABLE WORKING RULES

1. **Never fabricate data.** Never present a guess, estimate, or plausible-sounding number as verified fact.

2. **Never mark work "done" without showing the code that proves it.** Antigravity marked features "✅ Complete" while the function bodies were empty stubs (NWS forecast returned `null`; portfolio functions were bare signatures), then said "None added yet" one message later. It also falsely claimed the OBI meter and Portfolio didn't exist in the AI Studio version — disproved by reading the real code. **Neither Antigravity nor ChatGPT could verify the app's true state. Only reading the actual files can.**

3. **Verify external factual claims before building on them.** Apply this equally to every tool. ChatGPT and Perplexity outputs were checked with the same skepticism as Gemini's, and both produced errors that were caught this way.

4. **Work in discrete steps.** One change, then stop and report with a real diff. The user's "always allow, don't ask, just do it" mode in Antigravity is exactly what let fabricated ✅ claims through.

5. **Scope discipline.** Do not modify files outside the stated task, even cosmetically. This has been violated repeatedly (see History §Step 3).

6. **Auto-Execute / live trading gate.** Real-money automated trading may only be enabled after ALL THREE of:
   - 30+ resolved predictions with a Brier score meaningfully beating the market baseline
   - A walk-forward backtest shown with real numbers
   - The user typing the literal phrase **"enable live trading"**

   Never implied by "continue," "keep working," "it's done," or "once it's fully built." That last phrasing was explicitly rejected as a moving target — an agent told "start trading once it's done" will eventually decide it's done, because that is what finishing looks like to it.

---

# PART III — VERIFIED KALSHI FACTS

Confirmed against live documentation and API responses.

## API

- **Base URL:** `https://external-api.kalshi.com/trade-api/v2` — public reads need no key
- **Endpoints in use:** `/series/{ticker}`, `/markets?series_ticker=X&status=open`, `/markets/{ticker}`, `/markets/{ticker}/orderbook`, `/markets/{ticker}/candlesticks`, `/events/{ticker}`, `/portfolio/balance`, `/portfolio/positions`, `/portfolio/orders`
- **JSON fields:** `yes_bid_dollars`, `yes_ask_dollars` etc. are **string decimals**, not numbers. Also `volume_fp`, `close_time`, `expiration_time`, `result`, `status`.
- **Signing:** RSA-PSS, SHA-256, **salt length 32**

## Fees

**Taker:**
```
fee = roundUp(multiplier × 0.07 × contracts × price × (1 − price))
```
Price in dollars. Multiplier 1.0 default, 0.5 for S&P/Nasdaq index series. Round **UP** to the nearest cent.

Verified: 100 contracts @ 50¢ = `1 × 0.07 × 100 × 0.5 × 0.5 = 1.75` → exactly **$1.75**.

**Floating-point trap:** naive `Math.ceil(rawFee * 100) / 100` produced **$1.76** instead of $1.75 because `0.07 × 100 × 0.5 × 0.5` lands microscopically above 1.75 in IEEE 754. Fixed with an epsilon guard:
```
Math.ceil((rawFee * 100) - 1e-8) / 100
```

**Maker: NOT $0.00.** A build tool claimed maker orders "pay 0% fees ($0.00) on standard markets." **This was false** and was caught by independent web verification. Reality:
- Kalshi's own help center: maker fees apply to *"some markets"* — conditional, not universally zero
- Real worked example: **200 contracts @ 49¢ maker = $0.88**
- Reverse-engineered coefficient: **~0.0175** (≈¼ of taker). Verified: `0.0175 × 200 × 0.49 × 0.51 = 0.87465` → rounds to **$0.88**, matching exactly.
- The "$0.00" impression comes from small contract counts rounding down to zero cents — a rounding artifact of a small real fee, not a rule.

**This must stay labeled in the UI as an estimate.** Current label: `Estimated ~1/4 taker rate`, with the source data point cited on screen. Do not upgrade it to a stated fact.

## Orderbook — critical quirk

The API returns **BIDS ONLY for both sides.** The ask for one side must be derived as the complement of the opposite side's bid:
```
YES-ask = 1.00 − NO-bid
NO-ask  = 1.00 − YES-bid
```
Arrays are ascending, so **the best bid is LAST**. Reverse after complementing. This cross-side complement logic was verified correct in the current code.

## Tickers encode a fixed date

`KXHIGHNY-24JAN01-T60` = New York high temperature, **January 1 2024**, threshold 60°F.

Expired tickers return no live orderbook. This caused a long false-bug investigation (see History). The app currently does **not** warn about this — see Open Items A.

## Deep links

`https://kalshi.com/markets/{series_ticker_lowercase}` — confirmed working. No confirmed per-market URL format exists.

## Calibration research (verified real)

Kalshi market calibration across ~2.24M resolved markets: Brier ≈ 0.08–0.09 at three months out, tightening to ≈ 0.02 near close. **The market is a strong benchmark near resolution.** Any claimed personal edge must beat this, not just be "good."

---
# PART IV — COMPLETE BUILD HISTORY

Chronological. Every item marked verified was checked by reading real code or real screenshots, never by accepting a summary.

## Phase 1 — Early bug fixes (pre-roadmap)

**Fee floating-point overshoot** — `$1.76` where the answer was `$1.75`. Root cause: IEEE 754 representation pushing the product a hair above the boundary before `Math.ceil`. Fixed with a `1e-8` epsilon subtraction.

**Kelly convention disagreement** — the AI used fee-inclusive total cost (~6.7%) rather than raw price. Claude reviewed and **agreed the AI's version was more correct** than Claude's original raw-price formulation. Recorded because it is an instance where the code-gen tool was right and the reviewer was wrong.

**Percentage rounding at half-boundaries** — `formatPercent` mishandled exact `.5` cases.

**Impossible-input validation** — entering a blank price, 0 contracts, or a 150% probability produced a confident "+150% edge" display. Now the Analysis card hides entirely on invalid input rather than rendering nonsense.

**Broken series-multiplier fetch URL** — an empty ticker produced a request that hit Vite's SPA fallback, which returned **HTML that was then parsed as JSON**. This is the origin of the defensive fetch pattern used throughout `api.ts` (check `response.ok`, verify `content-type` includes `application/json`, catch, `console.warn`, return `null`). Keep this pattern on every new fetch.

**Bid/ask cross-side complement** — verified correct in code (see Verified Facts).

**Order-book depth walking + liquidity-trap warnings** — the app simulates walking real book depth for the exact contract count rather than assuming the top-of-book price fills the whole order.

**Prediction Log with Brier scoring and mandatory thesis** — the "My Thesis" field is genuinely required; the Log button is verified disabled until it is non-empty. This is deliberate: a prediction without a stated reason is not testable.

**Historical weather base rates** — Open-Meteo 10-year archive. Two results that looked like bugs were hand-checked against raw data and are **correct**: Miami 0% for 95°F (coastal temperature cap) and Austin 0% for T109. Do not "fix" these.

**Settlement details displayed verbatim** — no paraphrasing of Kalshi's settlement rules.

**Book-cross arbitrage check** — detects when the book is crossed.

**FOMC calendar was FABRICATED** — hardcoded dates carrying a fake "Source: Federal Reserve" label. Caught and replaced with real per-market Kalshi `close_time`/`expiration_time` values, or an honest "not configured" state when unavailable. This is the single clearest example of why rule #1 exists.

**Evidence Panel** — real Google News RSS headlines. Verified real, not synthesized.

## Phase 2 — External strategy input

**ChatGPT deep-research strategy document** — genuinely valuable. Sound ideas adopted:
- Separate *fair* probability (midpoint) from *executable* probability (real fill after fees)
- Train/validate/test firewall before any live "learning"
- Backtest before trusting any strategy
- Credential security concern: XOR/base64 is not encryption, and the private key was flowing browser → server. **Confirmed against the real `server.ts`.**

Its proposed ordering put the ensemble/prediction-engine first. **This was reordered — ensemble moved last.** You cannot responsibly combine signals into a weighted ensemble before testing whether each signal is worth anything alone; doing so produces a confident-looking number built on nothing.

## Phase 3 — The verified roadmap

### Step 1 — Credential security ✅ VERIFIED
- `src/utils/crypto.ts` created: real Web Crypto RSA-PSS SHA-256 signing, salt length 32, correct **PKCS#1 → PKCS#8 conversion** (commonly skipped or done wrong), graceful `null` return rather than silently signing garbage
- Private key never leaves the browser — verified `server.ts` contains **zero** occurrences of `privateKey`. Both the order route and the shared portfolio request helper read only `x-kalshi-signature` and `x-kalshi-timestamp` headers.
- XOR/base64 obfuscation retired. It survives in `store.ts` **only as a one-way migration shim** so pre-existing saved credentials still load; all new writes are plain. This was checked specifically because a leftover active path would have meant the fix didn't land.
- Security banner added in Settings stating credentials are stored locally and device security is the user's responsibility.

### Step 2 — Fair vs executable probability ✅ VERIFIED
- `fairProbabilityPct = (bestBidCents + bestAskCents) / 2` — an independent calculation, not aliased to the executable figure
- Executable breakeven = depth-walked average fill price + fees for the exact entered size
- Both shown side by side, gap displayed as slippage/fee friction. Never blended.
- **Critical check performed:** `handleLogPrediction` computes its own midpoint and never reads `liveResult.breakeven`. The Prediction Log therefore still snapshots the size-independent fair price. Had this been wired wrong, calibration history would have silently become inconsistent between old and new entries with no visible symptom.

### Step 3 — Market-specific fees ✅ VERIFIED (after correcting a false claim)
- Per-series multiplier now fetched everywhere. Previously the Sizer and standalone BookCrossCheck defaulted to 1.0x without querying series metadata.
- `OrderRole = 'taker' | 'maker'` type added to `math.ts`; toggle added to the Sizer
- **The maker-fee claim was wrong and was rejected.** See Verified Facts. Corrected to the 0.0175 coefficient with honest on-screen labeling citing the source data point.
- `simulateOrder` fixed: previously rounded fees **at each depth level** and summed the rounded values. Now sums raw unrounded slice fees and applies a single ceiling round at the transaction level.
- **Scope violation noted:** four files were modified without being asked — `Scanner.tsx`, `Watchlist.tsx`, `SettlementDetails.tsx`, `OBIFrictionMeter.tsx`. All changes were verified purely cosmetic (spacing, hover states, a tooltip, one label rename to "Settlement Details & Rules"). No logic touched. Harmless, but recorded because unscoped drift is exactly what "always allow" mode makes easy to miss.

### Step 5 — Immutable historical archive ✅ VERIFIED
*(Deliberately run before Step 4. Claude initially sequenced calibration polish ahead of storage, then corrected: every day without storage loses resolution data permanently, and nothing downstream is possible without it. The ordering mistake was acknowledged, not quietly reshuffled.)*

- `archiveResolvedMarket()` in `store.ts` is **genuinely append-only.** Verified: dedupes by `archiveId` OR `ticker + interactedAt`, returns `false` if the record exists, and the only write is `[record, ...current]` — a pure prepend. No edit or delete path exists anywhere in the file.
- `finalSettledOutcome` sourced **strictly** from Kalshi's `m.result`. No user-editable path, no default fallback, no manual "mark resolved" button.
- Storage keys: `kalshi_resolved_markets_archive_v1` (archive), `kalshi_tracked_interactions_v1` (pre-resolution buffer)
- Schema `ResolvedMarketRecord` in `types.ts`; sync in `settlementSync.ts`; UI in `HistoricalResolvedArchive.tsx`; JSON + CSV export exist
- **Caveat recorded at the time:** `orderBookSnapshot` is optional. Some records will have full depth and some will not. Backtests must handle missing snapshots explicitly rather than substituting a default.

### Step 4 — Calibration analytics ✅ VERIFIED
Run after Step 5, once there was a real dataset to analyse.

- **Log loss** added: `−[y·ln(p) + (1−y)·ln(1−p)]` with `LOG_LOSS_EPSILON = 0.001` clamping p to `[0.001, 0.999]`. Without the clamp, a single prediction logged at exactly 0% or 100% that resolved the other way would produce `Infinity` and silently destroy the average. Verified present, correct, and actually *called* — in the overall score, the category breakdown, the horizon breakdown, and both export paths. It also computes the market's log loss alongside the user's, giving a baseline comparison for free.
- **Category breakdown with override.** Auto-detection from ticker prefix (`KXFED`, `KXHIGHNY`, `INX`…) is the default; the user can manually override. Auto-detection from a deterministic prefix is acceptable — unlike a fuzzy guess, it is checkable — but it must be correctable so a misclassification doesn't quietly contaminate per-category calibration.
- **Verified the override does not break immutability.** `categoryOverride` lives only on the pre-resolution `Prediction` type. It is read once, at the moment a new `ResolvedMarketRecord` is constructed, and baked into `category`. There is no code path that reaches back into an already-archived record. Overriding *before* settlement is captured; overriding *after* leaves the archive frozen — which is correct behaviour for a reproducible dataset.
- **Horizon buckets** — `<24h`, `1–7d`, `7–30d`, `30+d`, computed from `close_time − log timestamp`
- **Small-sample gating is a real structural guard,** not a label. Below 5 resolved records, `avgBrier` and `avgLogLoss` are set to `null` rather than computed and hidden. A 2-record category structurally cannot emit a real-looking average through any path, including exports.
- **No blended composite "skill score" anywhere** — deliberate. Every breakdown stays separate so the user draws their own conclusions.

### Step 6 — Walk-forward backtest scaffold ✅ VERIFIED
- `src/utils/backtesting.ts` + `src/WalkForwardBacktest.tsx`
- `MIN_BACKTEST_RECORDS = 20`, enforced by a **real early return** with `timeSeries: []` before any computation. No partial or extrapolated output below threshold.
- **No-lookahead guard:** filters on `archivedAt <= cutoffMs`. This anchor is correct precisely because a record can only enter the archive once its outcome is already known, so future information cannot leak backward into an earlier cutoff point.
- The weekly sweep calls the same guarded `evaluateCutoffWindow` at every step — no bypass path
- UI branches on `isEligible` in multiple places, including a dedicated ineligible render. No hardcoded placeholder chart underneath.
- **Expected current behaviour: it shows the insufficient-data message.** That is correct, not a bug.

### Max-entropy distribution utility ✅ VERIFIED BY EXECUTION
Built because a Perplexity research document proposed using a two-outcome linear interpolation to convert Fed Funds futures into Kalshi probabilities. **That method is mathematically invalid with 3+ live outcomes** — one equation, two free parameters, underdetermined. There is no unique solution.

Correct approach: maximum entropy subject to the known mean — the least-informative distribution consistent with what is actually known.
```
p_i ∝ exp(−λ · r_i),  solve λ numerically so that Σ(p_i · r_i) = targetMean
```

`solveMaxEntropyDistribution(outcomes: number[], targetMean: number): number[] | null` in `math.ts`. Bisection, no external libraries, numerically stable (subtracts max exponent before `Math.exp`). Returns `null` for out-of-range targets, fewer than 2 outcomes, or non-convergence.

**Verified by extracting the real function, compiling it, and running it** — not by reading it. For `outcomes = [3.625, 3.375, 3.125]`, `targetMean = 3.529`:
```
[0.692725597687337, 0.23054623420996492, 0.07672816810269809]
sum = 1
weighted mean = 3.52899935739616
```
Matches an independent Python calculation to four decimals. Edge cases confirmed: out-of-range → `null`, single outcome → `null`, exact-boundary target → `[1, 0, 0]`.

**Currently unwired by design.** No UI, no data source. If ever surfaced it must be labeled: *"Modeled distribution (maximum entropy) — an estimate, not a direct market read."*

### Market Discovery view
Built from a Perplexity research document, but **deliberately narrowed.** That document proposed a weighted composite volatility score:
```
0.35·|Δp5m| + 0.25·|Δp15m| + 0.20·quote_intensity + 0.10·volume_accel + 0.10·liquidity_quality
```
**These weights are invented** — no derivation, no backtest, no citation, presented to two decimals so they look calibrated. Same failure pattern as the original fabricated sentiment scores, in more sophisticated clothing. Its filter thresholds (`spread ≤ 0.03`, `≥10 quote updates/5min`) have the same problem.

What was built instead: raw separate columns (spread, 24h range from real candlesticks, volume labeled explicitly as a liquidity indicator not volatility, time to close), single-column sorting only, no composite, and a required on-screen label — *"Discovery Aid — Sorts by real, observable metrics. Not a validated signal. Always evaluate manually before acting."* Clicking a row opens it in the Sizer; the view itself logs nothing and generates no probability, confidence, or thesis.

## Phase 4 — Bugs found in this session

### The `onClick` regression (real bug, fixed)
Symptom: typing a ticker into the Sizer and clicking Load did nothing.

Root cause: Market Discovery required `handleLoadTicker` to accept an optional ticker argument, so its signature became `handleLoadTicker(targetTicker?: string)`. But the manual Load button still had `onClick={handleLoadTicker}` — passing the function directly. React passes the click event as the first argument, so `targetTicker` silently received a `SyntheticEvent` object instead of `undefined`, and the ticker-fetch logic short-circuited on a truthy-but-wrong value.

*(Note: the handoff document, as received in this session, was truncated after this sentence. Parts V, VI, and VII were provided separately and are reproduced in full below. Any remaining Phase 4 items beyond the `onClick` regression, and any content of a hypothetical Part VIII or later, were not transmitted and are not represented in this document.)*

---

# PART V — OPEN ITEMS

Ranked by real risk. Each has an exact location.

## A. No expired-market warning — HIGHEST VALUE

`PositionSizer.tsx` contains **zero** references to `status`, `close_time`, or any expiry check. The API response carries this data; the app ignores it and falls through to *"No active offers available to fill this order"* — which reads as thin liquidity, not "this market closed 20 months ago."

This is the failure class the whole project exists to prevent: **the app knowing something and not telling you.**

**Fix:** on load, check `status` and `close_time`. If not open, or close_time is past, show a prominent banner in place of the generic message:
> "This market is closed or expired (closed [date]) — live pricing and order simulation are unavailable."

## B. Theoretical mode logs a fabricated market price with no warning

Confirmed: no warning text exists anywhere near Manual/Theoretical mode.

In `handleLogPrediction`:
```ts
if (mode === 'manual' && typeof priceCents === 'number') {
    marketProb = priceCents;              // ← the user's OWN typed number
} else if (mode === 'live' && orderBook) {
    marketProb = Math.round((bestBid + bestAsk) / 2);   // ← real market data
}
```
The Log Prediction button is equally available in both modes. Logging in Theoretical mode compares the user's guess against *their own guess of the market* — silently corrupting the calibration dataset. Manual mode will even log with a blank ticker as `"Manual Entry"`.

**Fix:** visible warning above the Log Prediction button in Theoretical mode:
> "Theoretical mode logs your typed price as the market price — this is not real market data and will distort calibration scoring. Use Live Orderbook mode for predictions you intend to score."

## C. Settlement guard is looser than it was described as

`settlementSync.ts`, around line 64:
```ts
const isSettled = (rawResult === 'yes' || rawResult === 'no') ||
                  (status === 'settled' && (rawResult === 'yes' || rawResult === 'no'));
```
This is an **OR** — the first clause alone passes. A market with `result: "yes"` but `status: "active"` would be archived as a finalized settlement. During Step 5 this was described as requiring both conditions; the code does not.

Likely harmless in practice (Kalshi probably does not populate `result` pre-settlement), but this is the field every downstream calibration number trusts.

**Fix:** require BOTH — status must be `'settled'` AND result must be exactly `'yes'` or `'no'`.

## D. Binary coercion on settlement outcome

`settlementSync.ts`, line 68:
```ts
const settledOutcome: 'yes' | 'no' = rawResult === 'yes' ? 'yes' : 'no';
```
Safe under the current guard, but any future third Kalshi settlement state (voided, cancelled) would be silently written into the **permanent, immutable** archive as a real `'no'` — corrupting calibration and backtests with no visible error.

**Fix:** explicit check for exactly `'yes'` / exactly `'no'`. Anything else: skip archiving that record entirely and `console.warn` naming the unexpected value.

## E. `PROJECT_STATUS.md` does not exist

Recommended repeatedly, never created. Every session — including after a container reset mid-session — rebuilds context from scratch. This document is intended to fill that gap.

## F. No test suite

No `.test.*` or `.spec.*` files exist anywhere; no test runner is installed. `npm run lint` (`tsc --noEmit`) is the only automated gate.

**Highest-value target if adding tests:** `src/utils/math.ts`. Fee calculation, Kelly sizing, Brier, log loss, and `solveMaxEntropyDistribution` are all pure functions with known-correct expected values documented in this file (100 contracts @ 50¢ → $1.75; 200 @ 49¢ maker → $0.88; max-entropy → `[0.6927, 0.2305, 0.0767]`).

---

# PART VI — THINGS THAT LOOK LIKE BUGS BUT ARE NOT

Do not "fix" these.

- **`KXHIGHNY-24JAN01-T60` showing no data.** Settled January 2024. Empty orderbook and a dash for live price are correct. The *message* is misleading (Open Item A); the data is not wrong.
- **NYC 0% historical rate for exceeding 60°F on Jan 1** across 2019–2023. Real. Verified against raw Open-Meteo data.
- **Miami 0% for 95°F.** Correct — coastal temperature cap.
- **Austin 0% for T109.** Correct.
- **"No active offers" on a genuinely thin market.** Honest output, not a failure.
- **Backtest showing "Insufficient historical data."** Correct — the archive has fewer than 20 resolved records.

---

# PART VII — REJECTED APPROACHES

Do not reintroduce.

- **Fabricated theses or mock prediction logs.** Requested and declined. A copy-pasted thesis is a null value in a required field. Calibration computed from generated predictions measures the generator while being labeled as the user's data, and every downstream conclusion about "where you have edge" would rest on it.
- **The weighted composite volatility score** from the Perplexity document. Invented weights, no derivation, no backtest, false precision.
- **Any blended overall "skill score"** in the calibration view.
- **Presenting maker fees as $0.00.**
- **Ensemble/prediction-engine before signal validation.** Moved to last on the roadmap for a reason.
- **"Once it's fully built out, enable auto-trading."** Rejected as a moving target. See Working Rule 6.

---
