import { describe, expect, it } from 'vitest';
import { solveMaxEntropyDistribution } from './maxent';

describe('solveMaxEntropyDistribution', () => {
  it('matches the handoff\'s independently-verified worked example (Part IV) to 4+ decimals', () => {
    const result = solveMaxEntropyDistribution([3.625, 3.375, 3.125], 3.529);
    expect(result).not.toBeNull();
    const weights = result ?? [];
    expect(weights[0]).toBeCloseTo(0.692725597687337, 4);
    expect(weights[1]).toBeCloseTo(0.23054623420996492, 4);
    expect(weights[2]).toBeCloseTo(0.07672816810269809, 4);

    const sum = weights.reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1, 10);

    const weightedMean = [3.625, 3.375, 3.125].reduce((acc, r, i) => acc + r * (weights[i] ?? 0), 0);
    expect(weightedMean).toBeCloseTo(3.529, 6);
  });

  it('returns null for a target outside the outcome range', () => {
    expect(solveMaxEntropyDistribution([1, 2, 3], 0.5)).toBeNull();
    expect(solveMaxEntropyDistribution([1, 2, 3], 3.5)).toBeNull();
  });

  it('returns null for fewer than 2 outcomes', () => {
    expect(solveMaxEntropyDistribution([], 1)).toBeNull();
    expect(solveMaxEntropyDistribution([5], 5)).toBeNull();
  });

  it('returns a one-hot distribution at the exact upper boundary target', () => {
    // 3.625 is the maximum of this outcome set - the only way to hit that
    // mean exactly is to put all weight on it.
    const result = solveMaxEntropyDistribution([3.625, 3.375, 3.125], 3.625);
    expect(result).toEqual([1, 0, 0]);
  });

  it('returns a one-hot distribution at the exact lower boundary target', () => {
    const result = solveMaxEntropyDistribution([3.625, 3.375, 3.125], 3.125);
    expect(result).toEqual([0, 0, 1]);
  });

  it('handles more than 3 outcomes and an off-center target', () => {
    const outcomes = [1, 2, 3, 4, 5];
    const result = solveMaxEntropyDistribution(outcomes, 1.5);
    expect(result).not.toBeNull();
    const weights = result ?? [];
    expect(weights.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 9);
    const mean = outcomes.reduce((acc, r, i) => acc + r * (weights[i] ?? 0), 0);
    expect(mean).toBeCloseTo(1.5, 6);
    // Least-informative distribution consistent with a low target mean
    // should weight the smaller outcomes more heavily.
    expect(weights[0] ?? 0).toBeGreaterThan(weights[4] ?? 0);
  });

  it('returns the uniform distribution when the target is the arithmetic mean', () => {
    const outcomes = [10, 20, 30];
    const result = solveMaxEntropyDistribution(outcomes, 20);
    expect(result).not.toBeNull();
    const weights = result ?? [];
    for (const w of weights) {
      expect(w).toBeCloseTo(1 / 3, 6);
    }
  });
});
