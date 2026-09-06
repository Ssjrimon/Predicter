import { describe, expect, it } from 'vitest';
import { computeFee, MAKER_FEE_RATE_ESTIMATE, TAKER_FEE_RATE } from './fees';
import { dollars } from './money';

describe('TAKER_FEE_RATE', () => {
  it('is 0.07, per Kalshi documentation (handoff Part III)', () => {
    expect(TAKER_FEE_RATE).toBe(0.07);
  });
});

describe('computeFee — taker', () => {
  it('100 contracts @ 50c, default multiplier -> exactly $1.75 (handoff Part III worked example)', () => {
    const fee = computeFee({ contracts: 100, priceDollars: dollars(0.5), role: 'taker' });
    expect(fee).toBe(1.75);
  });
});

describe('computeFee — maker (estimate)', () => {
  it('200 contracts @ 49c -> exactly $0.88 (handoff Part III worked example)', () => {
    const fee = computeFee({ contracts: 200, priceDollars: dollars(0.49), role: 'maker' });
    expect(fee).toBe(0.88);
  });

  it('coefficient is the reverse-engineered ~0.0175, not the rejected $0.00 claim (handoff Part VII)', () => {
    expect(MAKER_FEE_RATE_ESTIMATE).toBe(0.0175);
    expect(MAKER_FEE_RATE_ESTIMATE).toBeGreaterThan(0);
  });
});

describe('computeFee — series multiplier', () => {
  it('applies a 0.5x index-series multiplier before rounding, not proportionally after', () => {
    // 0.5 * 0.07 * 100 * 0.5 * 0.5 = 0.875 raw dollars = 87.5 raw cents.
    // The "always round up" rule takes that to 88 cents, not 87 or 87.5 -
    // rounding is not proportional to the multiplier, by design (fee always
    // rounds up to the next whole cent, never to nearest).
    const fee = computeFee({
      contracts: 100,
      priceDollars: dollars(0.5),
      role: 'taker',
      multiplier: 0.5,
    });
    expect(fee).toBe(0.88);
  });
});
