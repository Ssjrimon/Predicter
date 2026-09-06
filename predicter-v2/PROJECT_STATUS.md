# Predicter v2 — Project Status

Clean-slate rebuild of Predicter (personal Kalshi prediction-market analysis
tool), per `PREDICTER_COMPLETE_HANDOFF.md` in the repo root. This file exists
because the original build was rebuilt from scratch every session, including
after container resets — see handoff Part V, item E. Update it at the end of
every stage, as part of that stage's diff.

**The repo root also contains an unrelated Android/Kotlin tree
(`app/`, `build.gradle.kts`, etc.).** Per the user, this is a dead branch from
early in the project — the real Predicter app was built in Google AI Studio
and lives only there, not in this repo. It is not the app the handoff
describes and is not touched by this rebuild. Ignore it entirely.

**No data is inherited from the original app.** The original app runs on
`aistudio.google.com`; this build runs on `localhost`. Different origins
mean separate `localStorage` — nothing transfers. The two key literals below
are kept for consistency only. The archive starts empty, so the backtest
correctly reports insufficient data (`MIN_BACKTEST_RECORDS = 20`) from day
one — this is expected, not a bug (handoff Part VI item).

**Do not fabricate progress here.** A stage is only checked off once
`npm run verify` (tsc --noEmit + full test run) passes and the actual diff
has been shown for review. See handoff Part II, rules 2 and 4.

## Non-negotiables carried forward (handoff Part II–III, Part V–VIII)

- Fair (midpoint) and executable (depth-walked) probability are never blended.
- Small-sample gating returns `null`, not a hidden label (min 5 for
  calibration averages, min 20 for backtest — handoff Part III/Step 4/6).
- No blended composite scores anywhere (no "skill score", no invented
  volatility weights).
- Archive is append-only: no update/delete function exists in `storage/archive.ts`.
- Settlement outcome sourced strictly from Kalshi: `status === 'settled'` AND
  a valid binary `result` — both required (AND, not OR). Unrecognized states
  are skipped and `console.warn`'d, never coerced to `'no'`.
- Fee formulas, worked examples, epsilon guard, bids-only orderbook
  complement, ascending-array ordering, and RSA-PSS salt length 32 are taken
  as verified fact from the handoff — not re-derived.
- Theoretical-mode predictions are logged with `source: 'user-typed'`,
  displayed with a warning, and **excluded** from calibration scores and the
  30-prediction live-trading count (user decision, this session).
- `src/trading/` contains only a README stating the live-trading gate
  verbatim. No trading code exists.
- localStorage keys are frozen and must never change:
  `kalshi_resolved_markets_archive_v1`, `kalshi_tracked_interactions_v1`.
  Kept for consistency only — no data is inherited from the original app
  (different origin, `aistudio.google.com` vs `localhost`). Archive starts
  empty (user decision, confirmed).

## Build stages

| # | Stage | Status |
|---|---|---|
| 0 | Scaffold: Vite, strict tsconfig, Vitest, trading gate README, this file | **done** |
| 1 | `money` + `fees` + `format` + tests | **done** |
| 2 | `orderbook`: complement, ordering, depth walk, `simulateOrder` + tests | **done** |
| 3 | `probability` (fair vs executable) + `sizing` + validation + tests | **done** |
| 4 | `scoring` + `category` + `horizon` + `calibration` gating + tests | **done** |
| 5 | `storage`: keys, append-only archive, interactions, settlement guard + tests | **done** |
| 6 | `backtesting` + tests | **done** |
| 7 | `data`: defensive http, Kalshi client, schema parsing, expired-market check | **done** |
| 8 | `crypto` + Express proxy (zero `privateKey` occurrences, asserted by test) | not started |
| 9 | React shell, mobile-first, Sizer + Theoretical-mode warning | not started |
| 10 | Discovery, Archive, Calibration, Backtest, Settings | not started |
| 11 | Max-entropy utility (unwired, labeled), final audit vs Part V/VI/VII | not started |

## Known open items being fixed (handoff Part V)

- [ ] A — expired-market banner in the Sizer (Stage 7/9)
- [ ] B — Theoretical-mode warning + exclusion from scoring (Stage 9) — decided:
      record with provenance, exclude from calibration and the 30-prediction gate
- [ ] C — settlement guard requires status AND result, not OR (Stage 5)
- [ ] D — no binary coercion; unrecognized settlement states skipped + warned (Stage 5)
- [x] E — this file
- [ ] F — real test suite covering the math layer (all stages)

## Regressions from Part VI to guard with named tests (do not "fix" these)

- Miami 0% base rate at 95°F — coastal cap, verified vs raw Open-Meteo data.
- Austin 0% base rate at T109.
- NYC 0% base rate for >60°F on Jan 1, 2019–2023.
- `KXHIGHNY-24JAN01-T60` showing no live data — market settled Jan 2024;
  the fix is a clearer message (item A), not different data.
- "No active offers" on a genuinely thin market is honest output.
- Backtest "Insufficient historical data" below 20 resolved records is correct.

## Do not reintroduce (handoff Part VII)

- Fabricated theses or mock/generated prediction logs.
- The weighted composite volatility score (`0.35/0.25/0.20/0.10/0.10`, or any
  other invented, undated weighting).
- Any blended overall "skill score" in the calibration view.
- Presenting maker fees as $0.00.
- Ensemble/prediction-engine work before per-signal validation (stays last).
- "Once it's fully built, enable auto-trading" — see `src/trading/README.md`.

## Stage 1 — what shipped

`src/domain/money.ts`, `fees.ts`, `format.ts` + colocated tests (15 tests,
all passing; `scaffold.test.ts` deleted, no longer needed). `tsc --noEmit`
clean.

- `roundUpToCent`: epsilon-guarded ceiling to the next cent (handoff Part
  III/IV). Both the historical $1.76 bug and its naive-code witness are
  encoded as regression tests, not just a passing case.
- `computeFee`: taker (0.07) and maker (0.0175, labeled an estimate in its
  own doc comment) — independently recomputed and matched against both of
  the handoff's worked examples ($1.75 @ 100×50c taker, $0.88 @ 200×49c
  maker) rather than assuming the handoff's stated results.
- `formatPercent`/`roundHalfUp`: fixes the exact-`.5` boundary bug via a
  pre-round nudge; test includes the classic `2.675` IEEE-754 case as the
  regression witness (`(2.675).toFixed(2)` returns `"2.67"` natively).

## Stage 2 — what shipped

`src/domain/orderbook.ts` + tests (9 new tests, 24 total, all passing).
`fees.ts` gained an exported `rawFee` (unrounded formula) so multi-level
orders and single orders share one formula instead of duplicating it.

- `normalizeOrderBook`: derives asks as the complement of the opposite
  side's bids, reverses ascending raw arrays to best-first — implemented
  in the exact sequence the handoff specifies (complement first, then
  reverse), not just an equivalent reordering, so it stays traceable
  against the documented steps.
- `simulateBuy`: walks book depth level by level for the exact requested
  size. Sums *raw* per-level fees and rounds once at the end — verified
  against a worked 3-level example where per-level rounding would have
  overcharged by a cent ($2.11 vs the correct $2.10), encoded as its own
  regression test rather than just asserting the correct answer.
- Liquidity trap handling: a request the book can't fill returns
  `fullyFilled: false` with the fields describing only the achievable
  partial fill — never an extrapolated full-size fill (handoff Part IV:
  "simulates walking real book depth... rather than assuming the
  top-of-book price fills the whole order"). An empty book returns
  `null` averages/fees rather than `0`, so "no fill happened" is never
  mistaken for "filled at $0".
- Caveat carried from Part VIII: this "round once per completed order"
  behavior is directionally safe but not confirmed to exactly match
  Kalshi's real matching engine (see the Unverified Claims section below).

## Stage 3 — what shipped

`src/domain/probability.ts`, `sizing.ts`, `validation.ts` + tests (21 new
tests, 45 total, all passing).

- `FairProbability` and `ExecutableBreakeven` are disjoint types — no
  shared shape, no function accepts both. `FairProbability` carries a
  `source: 'orderbook-midpoint' | 'user-typed'` tag permanently, which is
  what makes Theoretical-mode contamination (Part V item B) visible at the
  type level rather than a silent runtime risk — every fair-probability
  value is traceable to where it came from for the rest of its life.
- `computeExecutableBreakeven` returns `null` when nothing filled (never a
  fabricated 0%/100%), and reports a partial fill's real filled size
  rather than the originally requested size.
- `kellyFraction` uses the fee-inclusive cost basis convention the project
  adopted after Claude reviewed a code-gen tool's version and agreed it
  was more correct than Claude's own raw-price original — an explicit
  case of the reviewer being wrong, preserved in the doc comment so it
  doesn't quietly get "corrected" back by a future session.
- `validation.ts` structurally guards the exact three impossible inputs
  the handoff names (blank/NaN price, 0 contracts, 150% probability) —
  Stage 9's UI must check `valid` before rendering the Analysis card, per
  Part IV Phase 1.

## Stage 4 — what shipped

`src/domain/scoring.ts`, `category.ts`, `horizon.ts`, `calibration.ts` +
tests (20 new tests, 65 total, all passing).

- `logLoss` clamps to `[LOG_LOSS_EPSILON, 1-LOG_LOSS_EPSILON]` (0.001) so a
  boundary prediction (0% or 100%) can never produce `Infinity` and
  silently destroy an average — tested by asserting finiteness at the
  exact boundary, not just a passing mid-range case.
- `assignCategory`: deterministic prefix detection (`KXFED`, `KXHIGH*`,
  `INX`) with an explicit `source` tag and an override that always wins.
  Documented the one place this build extrapolates beyond a literally
  verified fact: `KXHIGH*` as a general prefix (vs. the single verified
  `KXHIGHNY`) is an inference, flagged as such in the doc comment, not
  presented as equally verified.
- `summarizeCalibration`: the `n < 5` gate runs *before* any Brier/log-loss
  math executes, returning `null` averages — not a computed value that
  gets hidden by a display condition. A dedicated test asserts the
  summary object has exactly three keys (`n`, `avgBrier`, `avgLogLoss`),
  guarding against a future session quietly adding a blended score field.

## Stage 5 — what shipped

`src/storage/keys.ts`, `types.ts`, `archive.ts`, `interactions.ts`,
`settlement.ts` + tests (23 new tests, 88 total, all passing). Added
`@types/node` (dev dependency) for the guard test's filesystem scan.

- Storage functions take an injected `KeyValueStore` rather than touching
  `window.localStorage` directly, so test fixtures (necessarily synthetic
  prediction records) can never leak into or be mistaken for a real
  archive.
- `keys.test.ts` doesn't just assert the two literals are correct — it
  scans every `.ts`/`.tsx` file under `src/` at test time and fails if
  either raw string appears anywhere outside `keys.ts`. Confirmed clean
  against the real tree (zero offenders) at the moment this stage landed.
- `archive.ts`'s exported surface is locked by a test to exactly
  `{readArchive, appendResolvedMarket, exportArchiveJson,
  exportArchiveCsv}` — there is no update or delete function to add by
  accident, structurally, not just by convention.
- `settlement.ts`: `parseSettlement` requires status AND result (not the
  historical OR), and `extractSettledOutcome` warns via `console.warn`
  only on a genuinely unrecognized state — verified with a spy, not just
  a returned-null assertion, so "warned" and "silently null" can't be
  confused with each other in review.

## Stage 6 — what shipped

`src/domain/backtesting.ts` + tests (8 new tests, 96 total, all passing).
This completes the pure math domain layer (Stages 1-6) — everything from
here through Stage 8 starts touching real I/O (network, disk, crypto).

- Deliberately defines its own `BacktestRecord` shape rather than
  importing the storage layer's `ResolvedMarketRecord` — the domain layer
  imports nothing outside itself (see the layer diagram in the original
  architecture plan). Whichever future UI glue calls this maps a real
  archive record into this minimal shape first.
- `MIN_BACKTEST_RECORDS = 20` gates before any computation, mirroring the
  calibration gate's structure from Stage 4 exactly.
- `evaluateCutoffWindow`'s no-lookahead filter (`archivedAt <= cutoffMs`)
  is tested directly against a 3-record fixture with staggered archive
  times, not just asserted as a property of the whole sweep — so the
  guard itself is provably doing the filtering, not something else
  coincidentally producing the right totals.
- Confirmed explicitly: an empty archive (day one of this rebuild, since
  no data is inherited — see Part IX) correctly reports ineligible with
  zero records. That is the expected startup state, not a defect.

## Stage 7 — what shipped

`src/domain/ticker.ts`, `expiry.ts`; `src/data/http.ts`; `src/data/kalshi/schema.ts`, `client.ts`
+ tests (24 new tests, 120 total, all passing).

- `parseTicker`: parses the series/date/threshold structure and is tested
  against the handoff's one literally verified example
  (`KXHIGHNY-24JAN01-T60` → Jan 1 2024). Kept as a pure domain module —
  no I/O — since it's just string parsing.
- `checkMarketExpiry` + `formatExpiryBannerMessage`: implements Part V
  item A directly. The banner text is a function, not a string re-typed
  wherever it's needed, specifically so the exact quoted wording can't
  drift by paraphrase later (the same discipline as "settlement details
  displayed verbatim" from Part IV). Only `status === 'open'` is treated
  as confirmed-open, because that's the one status literal the handoff
  actually confirms (Part III cites `?status=open` as a real API
  parameter) — anything else is treated as not-open rather than guessing
  at a "closed" enum.
- `data/http.ts`'s `fetchJson` is the defensive fetch pattern from Part IV
  Phase 1, tested against all four failure modes including the exact
  historical bug (an HTML response parsed as JSON via Vite's SPA
  fallback) as a named regression case.
- **A live verification attempt was made and blocked, not skipped.**
  Tried to fetch a real response from `external-api.kalshi.com` to check
  the market/orderbook JSON wire shape before writing the client against
  it. This session's outbound network policy returns a 403 on the CONNECT
  tunnel to that host (confirmed via the proxy's own status endpoint —
  `recentRelayFailures` shows `connect_rejected` / policy denial, not a
  timeout or DNS issue). So: `parseMarketSummary` is built with full
  confidence from the field names Part III actually confirms
  (`yes_bid_dollars`, `status`, `close_time`, `result`, etc.).
  `parseRawOrderbook`'s wire shape (`UnverifiedRawOrderbookResponse`) is
  a clearly-labeled placeholder, isolated to one function — correcting it
  once a real response is available touches nothing in the domain layer,
  which only ever sees the already-verified `RawOrderBook` shape from
  Stage 2.

## Unverified claims carried forward (handoff Part VIII — do not build on without checking)

- **Rounding once per completed order** (vs. per depth-slice) is
  *directionally* safe — the fee is provably equal or lower than per-slice
  rounding — but whether this exactly matches Kalshi's real matching engine
  behavior was never independently confirmed. Stage 2's `simulateOrder`
  implements round-once-per-transaction per the handoff's own build
  history, but this caveat must stay attached to that implementation, not
  be silently upgraded to a confirmed fact.
- CF Benchmarks crypto settlement ("60-second average of one-second
  observations") — third-party, unverified. Do not build timing-sensitive
  settlement logic on it.
- CME 30-Day Fed Funds futures historical data access — blocked, no known
  free source. Do not write fetch code against an assumed API.
- Any Fed-rate backtest has a hard sample-size ceiling: likely under 30
  testable events total (8 FOMC meetings/year, market history is short).
- **New this session:** `data/kalshi/schema.ts`'s
  `UnverifiedRawOrderbookResponse` (the `/markets/{ticker}/orderbook`
  response shape) is a placeholder, not a confirmed fact — this session's
  network policy blocks `external-api.kalshi.com` (a real 403, confirmed
  via the proxy status endpoint, not a guess). Verify against a live
  response and correct `parseRawOrderbook` before connecting real market
  data through this client. `parseMarketSummary`'s fields are NOT in this
  caveat — those field names are directly confirmed by handoff Part III.

None of Stages 1-11 as planned currently touch Fed-rate or crypto-specific
logic, so none of the above blocks anything in this build. Recorded so a
future stage doesn't build on them uncritically.

## Environment

- Dev server: port 5273 (not 5173, to avoid colliding with the original app
  if both run locally at once).
- Node 22, npm 10.
