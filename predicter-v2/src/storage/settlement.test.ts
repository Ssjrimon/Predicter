import { afterEach, describe, expect, it, vi } from 'vitest';
import { extractSettledOutcome, parseSettlement } from './settlement';

describe('parseSettlement', () => {
  it('requires BOTH status==="settled" AND a valid result - the AND fix for handoff Part V item C', () => {
    // The exact case the old OR bug let through: result populated but
    // status not yet 'settled'.
    expect(parseSettlement('active', 'yes')).toEqual({ kind: 'not-settled', status: 'active' });
  });

  it('returns "settled" only when both conditions hold', () => {
    expect(parseSettlement('settled', 'yes')).toEqual({ kind: 'settled', outcome: 'yes' });
    expect(parseSettlement('settled', 'no')).toEqual({ kind: 'settled', outcome: 'no' });
  });

  it('never coerces an unexpected result under status=settled to "no" (handoff Part V item D)', () => {
    expect(parseSettlement('settled', 'voided')).toEqual({
      kind: 'unrecognized',
      status: 'settled',
      result: 'voided',
    });
    expect(parseSettlement('settled', null)).toEqual({ kind: 'unrecognized', status: 'settled', result: null });
    expect(parseSettlement('settled', undefined)).toEqual({
      kind: 'unrecognized',
      status: 'settled',
      result: undefined,
    });
    expect(parseSettlement('settled', '')).toEqual({ kind: 'unrecognized', status: 'settled', result: '' });
  });

  it('treats any non-settled status as simply not-settled, regardless of result', () => {
    expect(parseSettlement('open', undefined)).toEqual({ kind: 'not-settled', status: 'open' });
    expect(parseSettlement('closed', 'no')).toEqual({ kind: 'not-settled', status: 'closed' });
  });
});

describe('extractSettledOutcome', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns the outcome for a genuinely settled market, without warning', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(extractSettledOutcome('settled', 'yes')).toBe('yes');
    expect(warnSpy).not.toHaveBeenCalled();
  });

  it('returns null for a not-yet-settled market, without warning (the common, expected case)', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(extractSettledOutcome('active', null)).toBeNull();
    expect(warnSpy).not.toHaveBeenCalled();
  });

  it('returns null AND warns for an unrecognized settlement state - never a silent "no"', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const outcome = extractSettledOutcome('settled', 'voided');
    expect(outcome).toBeNull();
    expect(outcome).not.toBe('no'); // the exact bug this guards against
    expect(warnSpy).toHaveBeenCalledTimes(1);
    expect(warnSpy.mock.calls[0]?.[0]).toContain('voided');
  });
});
