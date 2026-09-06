import type { SimulateBuyResult } from './orderbook';

/**
 * The midpoint of the live orderbook, or a user-typed guess at that
 * midpoint (Theoretical/manual mode). Size-independent by construction —
 * it never depends on how many contracts you intend to buy.
 *
 * `source` records provenance permanently. This is what makes handoff
 * Part V item B (Theoretical mode silently logging a fabricated market
 * price) structurally visible rather than silently wrong: a caller can
 * always tell, from the value alone, whether this came from a real
 * orderbook or from the user's own typed number.
 */
export interface FairProbability {
  readonly kind: 'fair';
  readonly pct: number; // 0-100
  readonly source: 'orderbook-midpoint' | 'user-typed';
}

export function fairProbabilityFromBook(bestBidCents: number, bestAskCents: number): FairProbability {
  return { kind: 'fair', pct: (bestBidCents + bestAskCents) / 2, source: 'orderbook-midpoint' };
}

export function fairProbabilityFromUserInput(pct: number): FairProbability {
  return { kind: 'fair', pct, source: 'user-typed' };
}

/**
 * The real, depth-walked breakeven price for an exact contract count,
 * including fees — deliberately a different type from {@link FairProbability}
 * with no shared shape and no function that accepts both, so "fair" and
 * "executable" can never be silently blended (handoff Step 2).
 */
export interface ExecutableBreakeven {
  readonly kind: 'executable';
  readonly requestedContracts: number;
  readonly filledContracts: number;
  readonly fullyFilled: boolean;
  /** Average fill price plus fee-per-contract, as a percent (0-100). */
  readonly breakevenPct: number;
}

/**
 * `null` when nothing filled — there is no breakeven for a fill of zero
 * contracts, and this must never be reported as 0% (which would read as
 * "certain to lose") or 100% (which would read as "certain to win").
 */
export function computeExecutableBreakeven(sim: SimulateBuyResult): ExecutableBreakeven | null {
  if (sim.filledContracts === 0 || sim.averagePriceDollars === null || sim.feeDollars === null) {
    return null;
  }
  const feePerContract = sim.feeDollars / sim.filledContracts;
  const breakevenDollars = sim.averagePriceDollars + feePerContract;
  return {
    kind: 'executable',
    requestedContracts: sim.requestedContracts,
    filledContracts: sim.filledContracts,
    fullyFilled: sim.fullyFilled,
    breakevenPct: breakevenDollars * 100,
  };
}
