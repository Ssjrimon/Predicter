export type SettlementVerdict =
  | { readonly kind: 'settled'; readonly outcome: 'yes' | 'no' }
  | { readonly kind: 'not-settled'; readonly status: string }
  | { readonly kind: 'unrecognized'; readonly status: string; readonly result: string | null | undefined };

/**
 * Requires `status === 'settled'` AND `result` exactly `'yes'`/`'no'` — an
 * AND. A prior build shipped an OR, where `result` alone (regardless of
 * status) was enough to pass, which every downstream calibration number
 * trusted without anyone knowing the guard was loose (handoff Part V item
 * C). No coercion: any other value under a `'settled'` status is
 * `'unrecognized'`, never silently mapped to `'no'` — a future third
 * Kalshi settlement state (voided, cancelled) must not be written into the
 * permanent archive as a fabricated loss (handoff Part V item D).
 */
export function parseSettlement(status: string, result: string | null | undefined): SettlementVerdict {
  if (status !== 'settled') {
    return { kind: 'not-settled', status };
  }
  if (result === 'yes' || result === 'no') {
    return { kind: 'settled', outcome: result };
  }
  return { kind: 'unrecognized', status, result };
}

/**
 * Convenience wrapper for callers that just want an outcome or `null`.
 * Warns only on the `'unrecognized'` branch — a market that simply hasn't
 * settled yet is the common, expected case and produces no warning.
 */
export function extractSettledOutcome(status: string, result: string | null | undefined): 'yes' | 'no' | null {
  const verdict = parseSettlement(status, result);
  if (verdict.kind === 'settled') {
    return verdict.outcome;
  }
  if (verdict.kind === 'unrecognized') {
    console.warn(
      `[settlement] Unrecognized settlement state: status=${verdict.status}, result=${JSON.stringify(verdict.result)}. Skipping archive entry — not coerced to 'no'.`,
    );
  }
  return null;
}
