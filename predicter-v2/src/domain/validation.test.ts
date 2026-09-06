import { describe, expect, it } from 'vitest';
import { validateContracts, validatePriceDollars, validateProbabilityPct } from './validation';

describe('validateProbabilityPct', () => {
  it('rejects a blank/NaN price the way the historical bug did', () => {
    expect(validateProbabilityPct(NaN).valid).toBe(false);
  });

  it('rejects 150% - the exact impossible input that produced a fake "+150% edge" (handoff Part IV)', () => {
    const result = validateProbabilityPct(150);
    expect(result.valid).toBe(false);
  });

  it('rejects a negative probability', () => {
    expect(validateProbabilityPct(-5).valid).toBe(false);
  });

  it('accepts the full valid range including both boundaries', () => {
    expect(validateProbabilityPct(0).valid).toBe(true);
    expect(validateProbabilityPct(100).valid).toBe(true);
    expect(validateProbabilityPct(50).valid).toBe(true);
  });
});

describe('validateContracts', () => {
  it('rejects 0 contracts - the exact impossible input from the handoff', () => {
    expect(validateContracts(0).valid).toBe(false);
  });

  it('rejects a negative or fractional contract count', () => {
    expect(validateContracts(-1).valid).toBe(false);
    expect(validateContracts(1.5).valid).toBe(false);
  });

  it('accepts any positive whole number', () => {
    expect(validateContracts(1).valid).toBe(true);
    expect(validateContracts(1000).valid).toBe(true);
  });
});

describe('validatePriceDollars', () => {
  it('rejects a blank/NaN price', () => {
    expect(validatePriceDollars(NaN).valid).toBe(false);
  });

  it('rejects prices at or outside the $0/$1 boundary', () => {
    expect(validatePriceDollars(0).valid).toBe(false);
    expect(validatePriceDollars(1).valid).toBe(false);
    expect(validatePriceDollars(-0.1).valid).toBe(false);
    expect(validatePriceDollars(1.1).valid).toBe(false);
  });

  it('accepts a real price strictly between $0 and $1', () => {
    expect(validatePriceDollars(0.5).valid).toBe(true);
    expect(validatePriceDollars(0.01).valid).toBe(true);
    expect(validatePriceDollars(0.99).valid).toBe(true);
  });
});
