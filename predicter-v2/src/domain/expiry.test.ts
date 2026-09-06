import { describe, expect, it } from 'vitest';
import { checkMarketExpiry, formatExpiryBannerMessage } from './expiry';

describe('checkMarketExpiry', () => {
  it('is open when status is "open" and close_time is in the future', () => {
    const verdict = checkMarketExpiry({ status: 'open', closeTimeMs: 2000, nowMs: 1000 });
    expect(verdict).toEqual({ kind: 'open' });
  });

  it('is expired when close_time has passed, even if status is not otherwise recognized', () => {
    const verdict = checkMarketExpiry({ status: 'open', closeTimeMs: 1000, nowMs: 2000 });
    expect(verdict).toEqual({ kind: 'expired', closeTimeMs: 1000 });
  });

  it('is expired for the exact regression case from the handoff: a settled market (Part IV, Phase 4)', () => {
    // KXHIGHNY-24JAN01-T60, settled ~20 months before "now" in that story.
    const closeTimeMs = Date.UTC(2024, 0, 1);
    const nowMs = Date.UTC(2025, 8, 1);
    expect(checkMarketExpiry({ status: 'settled', closeTimeMs, nowMs })).toEqual({
      kind: 'expired',
      closeTimeMs,
    });
  });

  it('is expired for any status other than the one confirmed "open" literal', () => {
    const verdict = checkMarketExpiry({ status: 'unknown-status', closeTimeMs: 2000, nowMs: 1000 });
    expect(verdict.kind).toBe('expired');
  });
});

describe('formatExpiryBannerMessage', () => {
  it('matches the handoff banner text verbatim, with the date filled in', () => {
    const message = formatExpiryBannerMessage(Date.UTC(2024, 0, 1));
    expect(message).toBe(
      'This market is closed or expired (closed 2024-01-01) — live pricing and order simulation are unavailable.',
    );
  });
});
