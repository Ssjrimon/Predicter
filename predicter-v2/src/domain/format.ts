/**
 * A value that is mathematically an exact `.5` boundary is often stored as a
 * hair below it in IEEE 754 (the classic `2.675` case: stored as
 * `2.67499999999999982...`, so `2.675.toFixed(2)` returns `"2.67"`). A
 * previous build's `formatPercent` mishandled exactly these half-boundary
 * cases (handoff Part IV Phase 1). Nudging by a tolerance far larger than
 * any realistic representation error, before rounding, fixes both an
 * overshoot and an undershoot without affecting any non-boundary value.
 */
const HALF_UP_EPSILON = 1e-9;

export function roundHalfUp(value: number, decimals: number = 0): number {
  const factor = 10 ** decimals;
  const nudge = value >= 0 ? HALF_UP_EPSILON : -HALF_UP_EPSILON;
  return Math.round(value * factor + nudge) / factor;
}

/** `percentValue` is already on a 0-100 scale (e.g. 48.5, not 0.485). */
export function formatPercent(percentValue: number, decimals: number = 0): string {
  return `${roundHalfUp(percentValue, decimals).toFixed(decimals)}%`;
}
