# Predicter v2 — Project Status

Clean-slate rebuild of Predicter (personal Kalshi prediction-market analysis
tool). Built in `predicter-v2/`, alongside the original app, per
`PREDICTER_COMPLETE_HANDOFF.md` in the repo root. This file exists because the
original build was rebuilt from scratch every session, including after
container resets — see handoff Part V, item E. Update it at the end of every
stage, as part of that stage's diff.

**Do not fabricate progress here.** A stage is only checked off once
`npm run verify` (tsc --noEmit + full test run) passes and the actual diff
has been shown for review. See handoff Part II, rules 2 and 4.

## Non-negotiables carried forward (handoff Part II–III, Part V–VII)

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

## Build stages

| # | Stage | Status |
|---|---|---|
| 0 | Scaffold: Vite, strict tsconfig, Vitest, trading gate README, this file | **in progress** |
| 1 | `money` + `fees` + `format` + tests | not started |
| 2 | `orderbook`: complement, ordering, depth walk, `simulateOrder` + tests | not started |
| 3 | `probability` (fair vs executable) + `sizing` + validation + tests | not started |
| 4 | `scoring` + `category` + `horizon` + `calibration` gating + tests | not started |
| 5 | `storage`: keys, append-only archive, interactions, settlement guard + tests | not started |
| 6 | `backtesting` + tests | not started |
| 7 | `data`: defensive http, Kalshi client, schema parsing, expired-market check | not started |
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

## Environment

- Dev server: port 5273 (not 5173, to avoid colliding with the original app
  if both run locally at once).
- Node 22, npm 10.
