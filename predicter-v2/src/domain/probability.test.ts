import { describe, expect, it } from 'vitest';
import { computeExecutableBreakeven, fairProbabilityFromBook, fairProbabilityFromUserInput } from './probability';
import { normalizeOrderBook, simulateBuy } from './orderbook';

describe('fairProbabilityFromBook', () => {
  it('is the midpoint of best bid and best ask, tagged with its source', () => {
    const fair = fairProbabilityFromBook(48, 52);
    expect(fair).toEqual({ kind: 'fair', pct: 50, source: 'orderbook-midpoint' });
  });

  it('is independent of any contract size - it never takes one as input', () => {
    // Structural check: the function signature itself has no size
    // parameter, so a caller cannot accidentally make the fair price
    // depend on order size. This is a compile-time guarantee; this test
    // just documents intent alongside the type.
    const fair = fairProbabilityFromBook(10, 20);
    expect(fair.pct).toBe(15);
  });
});

describe('fairProbabilityFromUserInput', () => {
  it('carries source "user-typed", never conflated with a real market read', () => {
    const fair = fairProbabilityFromUserInput(63);
    expect(fair).toEqual({ kind: 'fair', pct: 63, source: 'user-typed' });
  });
});

describe('computeExecutableBreakeven', () => {
  it('is the depth-walked average price plus fee-per-contract, as a percent', () => {
    const book = normalizeOrderBook({ yesBids: [], noBids: [{ priceCents: 50, sizeContracts: 1000 }] });
    const sim = simulateBuy({ book, side: 'yes', contracts: 100, role: 'taker' });
    // averagePriceDollars = 0.50, feeDollars = 1.75 -> feePerContract = 0.0175
    // breakeven = 0.50 + 0.0175 = 0.5175 -> 51.75%
    const breakeven = computeExecutableBreakeven(sim);
    expect(breakeven).not.toBeNull();
    expect(breakeven?.breakevenPct).toBeCloseTo(51.75, 10);
    expect(breakeven?.filledContracts).toBe(100);
    expect(breakeven?.fullyFilled).toBe(true);
  });

  it('returns null when nothing filled - never a fabricated 0% or 100%', () => {
    const book = normalizeOrderBook({ yesBids: [], noBids: [] });
    const sim = simulateBuy({ book, side: 'yes', contracts: 50, role: 'taker' });
    expect(computeExecutableBreakeven(sim)).toBeNull();
  });

  it('reflects a partial fill honestly rather than the full requested size', () => {
    const book = normalizeOrderBook({ yesBids: [], noBids: [{ priceCents: 50, sizeContracts: 30 }] });
    const sim = simulateBuy({ book, side: 'yes', contracts: 100, role: 'taker' });
    const breakeven = computeExecutableBreakeven(sim);
    expect(breakeven?.fullyFilled).toBe(false);
    expect(breakeven?.filledContracts).toBe(30);
    expect(breakeven?.requestedContracts).toBe(100);
  });
});
