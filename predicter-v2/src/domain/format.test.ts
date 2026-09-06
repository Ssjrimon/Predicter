import { describe, expect, it } from 'vitest';
import { formatPercent, roundHalfUp } from './format';

describe('roundHalfUp', () => {
  it('rounds the classic 2.675 floating-point case correctly (naive toFixed fails this)', () => {
    expect(roundHalfUp(2.675, 2)).toBe(2.68);
    expect(Number(2.675.toFixed(2))).toBe(2.67); // the bug this guards against
  });

  it('rounds an exact .5 percentage up, not down (handoff Part IV Phase 1)', () => {
    expect(roundHalfUp(48.5, 0)).toBe(49);
    expect(roundHalfUp(49.5, 0)).toBe(50);
  });

  it('leaves a non-boundary value unaffected', () => {
    expect(roundHalfUp(48.2, 0)).toBe(48);
    expect(roundHalfUp(48.7, 0)).toBe(49);
  });
});

describe('formatPercent', () => {
  it('formats an exact half-percent boundary correctly', () => {
    expect(formatPercent(48.5)).toBe('49%');
  });

  it('formats a whole percent unchanged', () => {
    expect(formatPercent(50)).toBe('50%');
  });
});
