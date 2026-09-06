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
| 8 | `crypto` + Express proxy (zero `privateKey` occurrences, asserted by test) | **done** |
| 9 | React shell, mobile-first, Sizer + Theoretical-mode warning | **done** |
| 10 | Discovery, Archive, Calibration, Backtest, Settings | **done** |
| 11 | Max-entropy utility (unwired, labeled), final audit vs Part V/VI/VII | **done** |
| 12 | Post-completion: Open-Meteo historical base-rate view (deferred item) | **done** |
| 13 | Live-verification tooling (`verify-live-tickers.ts`) + a real `fetchOrderbook` crash bug it found | **done** |

## Stage 13 — live-verification tooling + a real bug it found

Requested as a follow-up to Stage 12: actually attempt to check 20 live
tickers. Two more paths were tried and both hit real blockers worth
recording, plus one genuine production bug was found and fixed as a
direct result of building this tooling.

- **This sandbox**: re-confirmed blocked, and the raw response body is
  now informative: `"Host not in allowlist: external-api.kalshi.com. Add
  this host to your network egress settings to allow access."` This is
  an explicit per-environment **allowlist**, not a blanket firewall — per
  this session's own environment docs, network policy is a setting the
  user chooses when creating the environment. **Actionable fix**: add
  `external-api.kalshi.com` (and `archive-api.open-meteo.com`, for the
  weather feature) to this environment's network egress allowlist in its
  claude.ai/code settings, then re-run `npm run verify:live` from a
  session using that environment.
- **The "trusted network access" remote environment**: tried twice.
  Both attempts hit a human-confirmation gate before contacting an
  external host — a legitimate safety control this agent has no API path
  to click through, and correctly did not try to route around.
- **`scripts/verify-live-tickers.ts`** (+ `verify-live-tickers.test.ts`,
  12 new tests, 194 total): a real, runnable tool built from the
  already-tested app code (not a rewritten parallel implementation) that
  checks N live tickers against both flagged "unverified wire shape"
  assumptions and reports concretely which held up, printing raw JSON
  for any that didn't. Run via `npm run verify:live` (20 random open
  markets) or `npm run verify:live TICKER1 TICKER2 ...` (specific
  tickers). Smoke-tested against the real (blocked) network to confirm
  it degrades gracefully — reports the block clearly and exits 1,
  doesn't crash.
- **A real production bug found by writing this tool's own tests, not by
  inspection**: `fetchOrderbook` threw an uncaught `TypeError` if a real
  response didn't match the assumed
  `{ orderbook: { yes: [...], no: [...] } }` shape (`.yes`/`.no` access
  on `undefined` from `parseRawOrderbook`), instead of returning `null`
  like every other boundary in this app. This means the *actual app*,
  not just the verification script, would have crashed rather than
  showing an honest error if Kalshi's real orderbook response doesn't
  match the placeholder shape — exactly the failure mode `fetchJson`'s
  defensive pattern exists to prevent, except this throw happened one
  layer downstream of it, outside that pattern's reach. Fixed by wrapping
  `parseRawOrderbook`'s call in `fetchOrderbook` with a try/catch,
  warning and returning `null` on any parse failure. Regression test
  added to `client.test.ts` feeding it a deliberately wrong shape and
  asserting it resolves to `null`, not a rejected promise.

## Stage 12 — deferred items follow-up

Requested after all 11 planned stages shipped: live-verify the Kalshi API
shapes, add the Open-Meteo weather base-rate feature, and settle the PR's
draft status.

- **Kalshi live verification: re-attempted, still blocked.** Re-ran the
  same check against `external-api.kalshi.com` — still a 403 on the
  CONNECT tunnel. The `recentRelayFailures` and the `curl` error text now
  make the blocker explicit: "connect_rejected (the egress proxy denied
  the CONNECT — organization policy)". This is a general outbound policy
  for this sandboxed session, not a Kalshi-specific denial — confirmed by
  also testing `archive-api.open-meteo.com`, which failed identically.
  `data/kalshi/schema.ts`'s `UnverifiedRawOrderbookResponse` caveat
  stands unchanged; nothing new to fix there.
- **Weather base-rate view added**: `domain/weatherLocations.ts`,
  `domain/baseRate.ts`, `data/openMeteo.ts`, `app/components/BaseRate.tsx`
  + tests (14 new tests, 185 total). Deliberately narrower than the
  original app: city is an explicit dropdown (New York / Miami / Austin),
  not inferred from the ticker prefix — the handoff confirms `KXHIGHNY`'s
  format but not Miami's or Austin's exact ticker prefixes, so this
  doesn't guess at them. Coordinates/timezones are treated as ordinary
  verified geographic facts (not the kind of claim needing a live-API
  check, unlike a JSON wire shape). The Open-Meteo response shape itself
  carries the same "unverified this session" caveat as the Kalshi client,
  for the same reason (network policy).
  - No-lookahead discipline applied to a data range, not just an archive
    cutoff: `endYear` is always the ticker's year minus one, so a base
    rate is never computed using data from the very day/year it's meant
    to inform about.
  - `null` (not a fabricated `0%`) when zero years of data are available —
    tested explicitly, mirroring the same discipline as
    `computeExecutableBreakeven` (Stage 3) and `summarizeCalibration`
    (Stage 4).
  - **Verified end-to-end in a real browser with the actual fetch
    pipeline exercised**: since the real host is also blocked, Playwright
    intercepted the request at the network layer (`page.route`) rather
    than mocking `fetch` in JS — the browser's real URL construction,
    query params, and headers all ran for real. The intercepted URL
    confirmed correct latitude/longitude, a `2014-01-01`–`2023-12-31`
    range (one year before the ticker's 2024), `temperature_unit=fahrenheit`,
    and the correct timezone. The computed result (30% — 3 of 10 seeded
    years exceeding 60°F) was independently hand-verified against the
    seeded fixture before trusting the screenshot.
  - Two real test-query bugs fixed along the way (not component bugs):
    the same `getByText`-matches-textarea-value collision as Discovery's
    Stage 10 test, and a `findByRole('alert')` collision between the
    view's persistent disclosure banner and its transient error message
    (both correctly use `role="alert"`, so the query needed
    disambiguating, not the component).
- **PR draft status**: updated the PR title/description to reflect full
  completion, confirmed the mergeability/CI check clean (no CI configured
  in this repo, no review comments), then marked it ready for review —
  reasonable now that every planned stage plus the deferred follow-up is
  done, tested, and pushed. Reversible with one click if the user wants
  more time before it's out of draft.

## Known open items — final status (handoff Part V)

- [x] A — expired-market banner: `domain/expiry.ts` (`checkMarketExpiry`,
      `formatExpiryBannerMessage`), wired in `useSizer.ts`/`Sizer.tsx`, tested
      at the unit level (Stage 7) and confirmed rendering in a real browser
      (Stage 9).
- [x] B — Theoretical-mode warning + exclusion from scoring: warning text
      (`THEORETICAL_MODE_WARNING`, verbatim) wired in Stage 9.
      **Exclusion was NOT actually wired until Stage 11's audit caught it** —
      `Calibration.tsx` and `Backtest.tsx` were scoring every archived record
      regardless of `marketProbabilitySource`, silently including
      Theoretical-mode predictions. Fixed by filtering to
      `marketProbabilitySource === 'orderbook-midpoint'` before any
      computation in both views, with a visible "Excludes N Theoretical-mode
      predictions" note, and regression tests proving the exclusion (a
      6-record archive with 1 Theoretical-mode record scores as n=5, not
      n=6; a Backtest archive of only Theoretical-mode records never becomes
      eligible). This is the single most consequential thing this audit
      found — a genuinely wrong number would have been shown had it shipped
      as originally built.
- [x] C — settlement guard requires status AND result, not OR: `storage/settlement.ts`, Stage 5.
- [x] D — no binary coercion; unrecognized settlement states skipped + warned: same file, Stage 5.
- [x] E — this file (Stage 0, maintained every stage since).
- [x] F — real test suite: 172 tests across every math/storage/data/UI module, all stages.

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

## Stage 8 — what shipped

`src/data/crypto.ts` (RSA-PSS signing) + `server/index.ts` (Express proxy)
+ tests (7 new tests, 127 total, all passing). Added `express`,
`@types/express`, `tsx` as dependencies; a `server` npm script.

- `signKalshiRequest` implements the PKCS#1→PKCS#8 DER conversion by hand
  (manual ASN.1 length encoding) and signs with RSA-PSS/SHA-256/salt 32.
  **Verified by actual execution, not just "doesn't throw":** the test
  generates a real 2048-bit RSA key pair via Node's `crypto` module,
  signs with our implementation, then independently imports the *public*
  key via Web Crypto and cryptographically verifies the signature against
  it — plus a negative control confirming a tampered message fails
  verification, so the positive test is proven meaningful rather than
  trivially passing.
- Caught and fixed a real bug via `tsc`, not by inspection: TS 5.7's
  stricter generic typed-array types made a bare `Uint8Array` annotation
  default to `Uint8Array<ArrayBufferLike>`, which Web Crypto's
  `BufferSource` (requiring concretely `ArrayBuffer`-backed views)
  rejected. Fixed with explicit `Uint8Array<ArrayBuffer>` annotations.
- **Caught and fixed a second real bug that `tsc` could NOT catch:**
  Express 5 (installed: v5.2.1) uses path-to-regexp v8, which dropped the
  bare `*` wildcard route syntax used by Express 4 (and by the original
  app, per its documented `npm run dev` convention). `app.all('/api/*', ...)`
  would have thrown at route-registration time — a runtime error no type
  checker can see, since it's a plain string. Caught by actually booting
  the server (`npm run server`) and confirming both the startup log line
  and a live request round-trip, not by trusting that `tsc --noEmit`
  passing meant the server worked.
- `server/index.ts` never accepts, stores, or forwards a signing
  credential — only the two header values the client already computed.
  Verified the same way the original project verified its own
  `server.ts`: a test scans this file's own source text for the
  credential-identifier spelling and asserts zero occurrences (handoff
  Part IV, Step 1). Hit the same self-referential trap as the Stage 5
  keys-literal guard: the file's own doc comment initially quoted the
  banned identifier while explaining why it's banned, tripping its own
  test — fixed by rephrasing the comment.

## Stage 9 — what shipped

`src/app/hooks/useSizer.ts`, `src/app/components/Sizer.tsx`, `App.tsx`,
mobile-first CSS + tests (12 new tests, 137 total, all passing). Also
fixed a real gap discovered while wiring the UI: `storage/types.ts` only
stored one probability number, but the handoff's calibration feature
needs both the user's own estimate and the market's fair probability
scored separately ("computes the market's log loss alongside the user's").
Split into `userEstimatePct` / `marketProbabilityPct` /
`marketProbabilitySource` before any real UI could write data in the
wrong shape; updated the Stage 5 test fixtures to match.

- The Theoretical-mode warning (`THEORETICAL_MODE_WARNING`, verbatim
  handoff text) lives in `domain/probability.ts` next to the `source` tag
  it's about, following the same verbatim-constant pattern as Stage 7's
  expiry banner.
- The Analysis card only renders once inputs validate — confirmed both
  in a component test (React Testing Library) and by driving a real
  headless Chromium against the actual `npm run dev` server.
- **A real bug was found and fixed by writing the tests, not by
  inspection:** the ticker `<input>` was disabled in Theoretical mode
  while `canLog` required a non-empty ticker in *both* modes — a user
  opening Theoretical mode directly (without ever visiting Live mode)
  could never satisfy `canLog` at all. Fixed by never disabling the
  ticker field; only the Live-mode Load button is mode-gated. A
  regression test locks this in.
- **Verified in a real browser, not just jsdom:** started the actual
  Vite dev server and drove it with a real headless Chromium (Playwright,
  pre-installed in this environment) at a mobile viewport (390×844) —
  screenshots sent to the user. Confirmed: the warning banner renders
  verbatim, the Analysis card's math matches Stage 1/3's known values
  exactly (100 contracts @ 50c → $1.75 fee → 51.75% cost basis; Kelly
  27.5% at p=0.65), the Log button enables/fires correctly, and the
  written `localStorage` record has the exact new schema. One console
  message appeared (`404` on `/favicon.ico`) — confirmed via `curl` to be
  the browser's automatic favicon probe against a route that doesn't
  exist yet, not a functional defect.
- Kept a hard distinction between `ExecutableBreakeven` (Stage 3, real
  depth-tested fills) and a new `TheoreticalCostEstimate` type (this
  stage) for the hypothetical single-price estimate Theoretical mode
  shows — deliberately not the same type, so a hypothetical estimate can
  never be mistaken for or handled like a real, depth-walked fill.
- Live-mode's Kelly suggestion is only computed when `fullyFilled` is
  `true` — a liquidity-trap partial fill shows its own warning instead of
  a Kelly number sized against an unfillable request.

## Stage 10 — what shipped

Five views (`Discovery.tsx`, `Archive.tsx`, `Calibration.tsx`, `Backtest.tsx`,
`Settings.tsx`), tab navigation in `App.tsx`, plus two supporting modules
this stage revealed were needed: `storage/credentials.ts` (plain-text
credential storage, per the corrected Step 1 convention — no fake
obfuscation) and `data/kalshi/settlementSync.ts` (ties the Stage 5
settlement guard to the Stage 7 client and the archive). 25 new tests,
162 total, all passing.

- **Archive**: read-only by construction — there is no edit/delete/"mark
  resolved" control because the underlying module exposes no such
  function. A test explicitly asserts none of those buttons exist.
- **Calibration**: You and Market are always two separate numbers, never
  one blended score — a test asserts no "skill score" text appears
  anywhere on the page (handoff Part VII), verified against real seeded
  data in a real browser, not just the unit-level gate.
- **Backtest**: verified against real seeded 20-record data in an actual
  browser session — the no-lookahead weekly sweep correctly produced
  `n=1 (insufficient data)` for the first cutoff window and `n=20` for
  the last, exactly matching the timestamps seeded. This is Stage 6's
  domain logic proven against realistic data end-to-end, not just its own
  narrow unit tests.
- **Discovery**: deliberately narrower than the original app. Could not
  verify the `/markets?series_ticker=...` list-response envelope or the
  candlestick response schema this session (same network block as Stage
  7), so rather than guess at those shapes, this view takes a manual
  ticker list and shows only spread + time-to-close — both backed by
  confirmed market-summary fields. The required verbatim label
  ("Discovery Aid — Sorts by real, observable metrics...") is present
  and tested; a test also asserts no composite/volatility-score text
  appears anywhere (handoff Part VII). Auto-discovery and a real 24h
  range can be added once those two shapes are verified against a live
  response — noted as a follow-up, not silently dropped.
- **Settings**: plain-text credential storage with an honest security
  disclosure, matching the original project's corrected Step 1
  convention (fake XOR/base64 "encryption" was retired specifically
  because it wasn't real security — the disclosure IS the security
  model here, not a placeholder for one).
- Two real bugs caught by writing tests, not by inspection: a test
  fixture that accidentally deduped 19 of 20 "distinct" archive records
  because it reused the same ticker+interactedAt pair (the dedupe logic
  was correct; the fixture was wrong), and a `getByText` match against a
  `<textarea>`'s own value colliding with a results row's text (fixed by
  querying the specific button role instead).
- Verified in a real browser: seeded 20 records directly via
  `localStorage` (there is no live settlement flow to populate the
  archive naturally without network access to Kalshi), navigated all six
  tabs, and confirmed Archive/Calibration/Backtest render correctly
  against that data. Screenshots sent to the user.

## Stage 11 — what shipped: max-entropy utility + final audit

`src/domain/maxent.ts` + tests (7 new tests, 172 total, all passing).
`solveMaxEntropyDistribution` independently reproduces the handoff's
verified worked example
(`[3.625, 3.375, 3.125]`, target `3.529` → `[0.6927, 0.2305, 0.0767]`) via
its own bisection implementation — matched to 4+ decimals without copying
the algorithm's stated output, only its description (p_i ∝ exp(-λ·r_i),
numerically stable via max-exponent subtraction). Confirmed genuinely
unwired: zero references anywhere under `src/app/`.

**Final audit against Parts V, VI, VII** — this is not a rubber stamp;
each item below was checked against actual code, and one real gap was
found and fixed (see item B above).

- **Part V** — all six items now `[x]`, see above. Item B's exclusion
  fix is the one substantive finding of this audit.
- **Part VI** (things that look like bugs but aren't) — the two items
  this rebuild has code for (expired-market handling, insufficient-data
  backtest/calibration on a small archive) are correctly implemented and
  tested throughout Stages 5-10. The other four items (Miami/Austin/NYC
  historical weather base rates via Open-Meteo) have **no corresponding
  feature in this rebuild at all** — the 11-stage plan never included an
  Open-Meteo integration or a historical base-rate view. Recorded here
  explicitly rather than silently: if that feature is ever added, these
  four base-rate results must be treated as verified-correct, not bugs to
  "fix," exactly as the handoff states.
- **Part VII** (do not reintroduce) — verified by grep sweep across the
  entire `src/` tree in addition to the reasoning above:
  - Fabricated theses/mock logs: no code generates thesis text anywhere;
    it is a required, user-typed field with no default or auto-fill.
  - Weighted composite volatility score: `Discovery.tsx` shows only raw
    spread and time-to-close, single-column-sortable; a test asserts no
    "volatility score" or "composite" text appears.
  - Blended skill score: grepped for `skillScore`/`compositeScore`/
    `weightedScore` across `src/` — zero matches. `Calibration.tsx` emits
    only separate Brier/log-loss numbers, tested.
  - Maker fees as $0.00: `MAKER_FEE_RATE_ESTIMATE = 0.0175`, tested to
    the exact worked example; grepped for `$0.00`-adjacent maker-fee
    phrasing — zero matches.
  - Ensemble before signal validation: no ensemble/prediction-combination
    code exists anywhere in this build — correctly never started.
  - "Once fully built, enable auto-trading": `src/trading/` contains
    exactly one file (`README.md`, the gate verbatim) — confirmed by
    listing the directory, not just by memory of having written it that
    way. Grepped for `markResolved`/`manualResolve`/`forceResolve` across
    `src/` to confirm no path exists for a user to hand-resolve a
    prediction either — zero matches, consistent with Part V item D.

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
- **New this session:** Discovery's original scope (auto-discover markets
  by series ticker; a 24h range from candlestick data) is deferred, same
  root cause — the `/markets?series_ticker=...` list-response envelope
  and the `/markets/{ticker}/candlesticks` response schema are unverified
  this session. Shipped instead: a manual ticker list scanning only
  spread + time-to-close, both backed by confirmed market-summary fields.

None of Stages 1-11 as planned currently touch Fed-rate or crypto-specific
logic, so none of the above blocks anything in this build. Recorded so a
future stage doesn't build on them uncritically.

## Environment

- Dev server: port 5273 (not 5173, to avoid colliding with the original app
  if both run locally at once).
- Node 22, npm 10.
