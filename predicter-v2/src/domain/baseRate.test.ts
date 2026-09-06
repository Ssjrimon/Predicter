import { describe, expect, it } from 'vitest';
import { computeExceedanceBaseRate } from './baseRate';

describe('computeExceedanceBaseRate', () => {
  it('computes the fraction of years strictly exceeding the threshold', () => {
    expect(computeExceedanceBaseRate([50, 61, 62, 59], 60)).toBe(0.5);
  });

  it('reproduces the handoff\'s verified 0% results as a real computed value, not a guess', () => {
    // Miami 95F and Austin T109 - "0%" is a genuine computed fraction here,
    // not a hardcoded special case, so a future dataset that DOES exceed
    // the threshold would correctly show a nonzero rate.
    expect(computeExceedanceBaseRate([88, 90, 91, 89, 92], 95)).toBe(0);
  });

  it('returns null for no data, never a fabricated 0%', () => {
    expect(computeExceedanceBaseRate([], 60)).toBeNull();
  });

  it('uses strict exceedance, not >=, matching a Kalshi "greater than" high-temp market', () => {
    expect(computeExceedanceBaseRate([60, 60, 60], 60)).toBe(0);
    expect(computeExceedanceBaseRate([60.1], 60)).toBe(1);
  });
});
