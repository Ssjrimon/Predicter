import { describe, expect, it } from 'vitest';
import { parseTicker } from './ticker';

describe('parseTicker', () => {
  it('parses the exact verified handoff example: NY high temp, Jan 1 2024, threshold 60', () => {
    const parsed = parseTicker('KXHIGHNY-24JAN01-T60');
    expect(parsed).not.toBeNull();
    expect(parsed?.seriesPrefix).toBe('KXHIGHNY');
    expect(parsed?.threshold).toBe('60');
    expect(new Date(parsed?.dateMs ?? 0).toISOString()).toBe('2024-01-01T00:00:00.000Z');
  });

  it('is case-insensitive', () => {
    expect(parseTicker('kxhighny-24jan01-t60')).toEqual(parseTicker('KXHIGHNY-24JAN01-T60'));
  });

  it('handles a non-integer threshold (e.g. a Fed rate)', () => {
    const parsed = parseTicker('KXFED-25JUN18-T5.25');
    expect(parsed?.threshold).toBe('5.25');
  });

  it('returns null for a malformed ticker rather than throwing or guessing', () => {
    expect(parseTicker('not-a-ticker')).toBeNull();
    expect(parseTicker('KXHIGHNY-24XYZ01-T60')).toBeNull(); // invalid month abbreviation
    expect(parseTicker('')).toBeNull();
  });
});
