import { describe, expect, it } from 'vitest';
import { brierScore, logLoss, LOG_LOSS_EPSILON } from './scoring';

describe('brierScore', () => {
  it('computes (p - y)^2 for known values', () => {
    expect(brierScore(0.7, 1)).toBeCloseTo(0.09, 10);
    expect(brierScore(0.3, 0)).toBeCloseTo(0.09, 10);
  });

  it('is 0 for a perfect prediction and 1 for a maximally wrong one', () => {
    expect(brierScore(1, 1)).toBe(0);
    expect(brierScore(0, 0)).toBe(0);
    expect(brierScore(0, 1)).toBe(1);
    expect(brierScore(1, 0)).toBe(1);
  });
});

describe('logLoss', () => {
  it('matches -ln(p) for a correct-direction prediction', () => {
    expect(logLoss(0.7, 1)).toBeCloseTo(-Math.log(0.7), 10);
    expect(logLoss(0.3, 0)).toBeCloseTo(-Math.log(0.7), 10); // 1 - 0.3 = 0.7
  });

  it('never produces Infinity at the exact 0%/100% boundary (handoff Part IV, Step 4)', () => {
    expect(Number.isFinite(logLoss(0, 1))).toBe(true);
    expect(Number.isFinite(logLoss(1, 0))).toBe(true);
    // Without the clamp this would be exactly -ln(0) = Infinity.
    expect(logLoss(0, 1)).toBeCloseTo(-Math.log(LOG_LOSS_EPSILON), 10);
    expect(logLoss(1, 0)).toBeCloseTo(-Math.log(LOG_LOSS_EPSILON), 10);
  });

  it('clamps values outside [epsilon, 1-epsilon] rather than trusting caller input', () => {
    // Defensive: even an out-of-range p (a caller bug) stays finite.
    expect(Number.isFinite(logLoss(-1, 1))).toBe(true);
    expect(Number.isFinite(logLoss(2, 0))).toBe(true);
  });
});
