import { describe, expect, it } from 'vitest';
import { computeHorizonBucket } from './horizon';

const HOUR = 3_600_000;
const DAY = 24 * HOUR;

describe('computeHorizonBucket', () => {
  it('buckets under 24h', () => {
    expect(computeHorizonBucket(DAY - 1, 0)).toBe('<24h');
    expect(computeHorizonBucket(HOUR, 0)).toBe('<24h');
  });

  it('buckets 1-7 days', () => {
    expect(computeHorizonBucket(DAY, 0)).toBe('1-7d');
    expect(computeHorizonBucket(7 * DAY - 1, 0)).toBe('1-7d');
  });

  it('buckets 7-30 days', () => {
    expect(computeHorizonBucket(7 * DAY, 0)).toBe('7-30d');
    expect(computeHorizonBucket(30 * DAY - 1, 0)).toBe('7-30d');
  });

  it('buckets 30+ days', () => {
    expect(computeHorizonBucket(30 * DAY, 0)).toBe('30+d');
    expect(computeHorizonBucket(365 * DAY, 0)).toBe('30+d');
  });

  it('falls into <24h defensively if close time is already at or before the log time', () => {
    expect(computeHorizonBucket(0, 0)).toBe('<24h');
    expect(computeHorizonBucket(-DAY, 0)).toBe('<24h');
  });
});
