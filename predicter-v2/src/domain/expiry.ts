/**
 * Handoff Part V item A: "on load, check status and close_time. If not
 * open, or close_time is past, show a prominent banner... in place of the
 * generic [no active offers] message." This is the failure class the whole
 * project exists to prevent — the app knowing something and not telling
 * you (a settled market silently producing "no active offers" instead of
 * "this closed 20 months ago").
 *
 * The one Kalshi status literal this handoff actually confirms is
 * `'open'` — Part III lists `/markets?series_ticker=X&status=open` as a
 * real, in-use API endpoint parameter. Anything else — including
 * `'settled'`, or any other status string — is treated as not-open here,
 * matching the handoff's literal "if not open" phrasing rather than
 * enumerating a guessed set of "closed" status values not confirmed by
 * this handoff.
 */
export interface ExpiryCheckInput {
  readonly status: string;
  readonly closeTimeMs: number;
  readonly nowMs: number;
}

export type ExpiryVerdict = { readonly kind: 'open' } | { readonly kind: 'expired'; readonly closeTimeMs: number };

export function checkMarketExpiry(input: ExpiryCheckInput): ExpiryVerdict {
  const isOpen = input.status === 'open' && input.closeTimeMs > input.nowMs;
  if (isOpen) {
    return { kind: 'open' };
  }
  return { kind: 'expired', closeTimeMs: input.closeTimeMs };
}

/**
 * The exact banner text from the handoff, verbatim, with the date filled
 * in — so the wording is never re-typed (and drifted) by whichever UI
 * component ends up rendering it.
 */
export function formatExpiryBannerMessage(closeTimeMs: number): string {
  const closedDate = new Date(closeTimeMs).toISOString().slice(0, 10);
  return `This market is closed or expired (closed ${closedDate}) — live pricing and order simulation are unavailable.`;
}
