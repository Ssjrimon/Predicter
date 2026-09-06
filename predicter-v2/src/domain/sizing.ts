import type { Dollars } from './money';

export interface KellyInput {
  /** The user's own probability estimate, 0-1 (not 0-100). */
  readonly trueProbability: number;
  /** Fee-inclusive cost per contract: fill price + fee-per-contract, in dollars. */
  readonly costBasisDollars: Dollars;
}

/**
 * f* = (p - c) / (1 - c), clamped to [0, 1].
 *
 * Uses a fee-inclusive cost basis, not raw price — the convention this
 * project adopted deliberately. A prior build used fee-inclusive total
 * cost; Claude's own original formulation used raw price instead, and on
 * review agreed the fee-inclusive version was more correct (handoff Part
 * IV, Phase 1) — an explicit case where the code-generation tool was right
 * and the human reviewer's first instinct was wrong. `costBasisDollars`
 * should come from an {@link import('./probability').ExecutableBreakeven}
 * (`breakevenPct / 100`), not the bare orderbook price.
 *
 * `p <= c` means no edge: returns 0, never a negative or "short" sizing
 * suggestion — this formula only models buying the side you believe in.
 */
export function kellyFraction(input: KellyInput): number {
  const { trueProbability: p, costBasisDollars: c } = input;
  if (p <= c) {
    return 0;
  }
  const raw = (p - c) / (1 - c);
  return Math.min(1, Math.max(0, raw));
}
