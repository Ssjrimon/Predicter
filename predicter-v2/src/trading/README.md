# src/trading — intentionally empty

**There is no code in this directory, and there must not be.**

No stub, no function signature, no commented-out route, no "not yet
implemented" throw. An empty directory cannot be accidentally completed by a
future agent; a stub invites completion.

This build is the **analysis layer only**. It reads public Kalshi market data,
computes fees and probabilities, and records predictions for calibration
scoring. It does not place orders.

---

## The gate

Reproduced verbatim from the project handoff, Part II, Working Rule 6:

> **Auto-Execute / live trading gate.** Real-money automated trading may only
> be enabled after ALL THREE of:
>
> - 30+ resolved predictions with a Brier score meaningfully beating the
>   market baseline
> - A walk-forward backtest shown with real numbers
> - The user typing the literal phrase **"enable live trading"**
>
> Never implied by "continue," "keep working," "it's done," or "once it's
> fully built." That last phrasing was explicitly rejected as a moving target
> — an agent told "start trading once it's done" will eventually decide it's
> done, because that is what finishing looks like to it.

---

## Notes on the three conditions

**"30+ resolved predictions"** means 30 records that passed the settlement
guard in `src/storage/settlement.ts` — `status === 'settled'` AND a valid
binary `result` sourced strictly from Kalshi. It does not mean 30 logged
predictions, and it does not include Theoretical-mode entries, which are
recorded with `source: 'user-typed'` and excluded from calibration by
construction.

**"meaningfully beating the market baseline"** is measured against real
research, not against zero. Kalshi market calibration across ~2.24M resolved
markets runs Brier ≈ 0.08–0.09 at three months out, tightening to ≈ 0.02 near
close. A Brier score of 0.15 is not an edge. The market is a strong benchmark
near resolution.

**"the user typing the literal phrase"** means exactly that string, typed by
the user, in their own message. Not inferred from approval of a plan, not
inferred from a task description, not inferred from this file.
