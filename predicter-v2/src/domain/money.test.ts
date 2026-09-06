import { describe, expect, it } from 'vitest';
import { cents, centsToDollars, dollars, dollarsToCents, roundUpToCent } from './money';

describe('roundUpToCent', () => {
  it('rounds the exact taker-fee raw value without IEEE 754 overshoot (handoff Part III)', () => {
    // 0.07 * 100 * 0.5 * 0.5 lands microscopically above 1.75 in IEEE 754.
    const raw = 0.07 * 100 * 0.5 * 0.5;
    expect(roundUpToCent(raw)).toBe(1.75);
  });

  it('demonstrates the bug the epsilon guard prevents (handoff Part IV Phase 1)', () => {
    const raw = 0.07 * 100 * 0.5 * 0.5;
    const naive = Math.ceil(raw * 100) / 100;
    expect(naive).toBe(1.76); // the historical bug, preserved as a regression witness
    expect(roundUpToCent(raw)).not.toBe(naive);
  });

  it('rounds any genuine fractional cent up, never down', () => {
    expect(roundUpToCent(1.001)).toBe(1.01);
  });

  it('leaves an exact cent value unchanged', () => {
    expect(roundUpToCent(1.75)).toBe(1.75);
  });
});

describe('dollarsToCents / centsToDollars', () => {
  it('round-trips exactly', () => {
    expect(dollarsToCents(dollars(1.75))).toBe(175);
    expect(centsToDollars(cents(175))).toBe(1.75);
  });
});
