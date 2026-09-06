import { describe, expect, it } from 'vitest';
import { kellyFraction } from './sizing';
import { dollars } from './money';

describe('kellyFraction', () => {
  it('computes a clean worked example: p=0.75, cost=0.50 -> f*=0.5', () => {
    expect(kellyFraction({ trueProbability: 0.75, costBasisDollars: dollars(0.5) })).toBe(0.5);
  });

  it('uses the fee-inclusive cost basis (handoff Part IV convention)', () => {
    // 100 contracts @ 50c taker: cost basis = 0.50 + 1.75/100 = 0.5175.
    // With p=0.60, f* = (0.60 - 0.5175) / (1 - 0.5175).
    const f = kellyFraction({ trueProbability: 0.6, costBasisDollars: dollars(0.5175) });
    expect(f).toBeCloseTo(0.17098445595854922, 10);
  });

  it('returns exactly 0 when there is no edge (p <= cost), never negative', () => {
    expect(kellyFraction({ trueProbability: 0.5, costBasisDollars: dollars(0.5175) })).toBe(0);
    expect(kellyFraction({ trueProbability: 0.5, costBasisDollars: dollars(0.5) })).toBe(0); // exact tie
  });

  it('clamps to 1 for a pathological caller input above the formula\'s natural range', () => {
    // p=1.5 is invalid input by construction (see validation.ts), but the
    // sizing function stays defensively bounded regardless of caller bugs.
    const f = kellyFraction({ trueProbability: 1.5, costBasisDollars: dollars(0.9) });
    expect(f).toBe(1);
  });

  it('reaches exactly 1 at the natural boundary p=1, cost=0', () => {
    expect(kellyFraction({ trueProbability: 1, costBasisDollars: dollars(0) })).toBe(1);
  });
});
