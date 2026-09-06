import { fetchJson } from '../http';
import type { ParsedMarketSummary, RawMarketSummary, UnverifiedRawOrderbookResponse } from './schema';
import { parseMarketSummary, parseRawOrderbook } from './schema';
import type { RawOrderBook } from '../../domain/orderbook';

/** Verified (handoff Part III): public reads need no key. */
export const KALSHI_BASE_URL = 'https://external-api.kalshi.com/trade-api/v2';

export async function fetchMarket(ticker: string): Promise<ParsedMarketSummary | null> {
  const raw = await fetchJson<RawMarketSummary>(`${KALSHI_BASE_URL}/markets/${encodeURIComponent(ticker)}`);
  if (raw === null) {
    return null;
  }
  return parseMarketSummary(raw);
}

/**
 * See `schema.ts`'s doc comment on `UnverifiedRawOrderbookResponse` — the
 * wire shape here is unverified. `parseRawOrderbook` reads nested fields
 * (`raw.orderbook.yes`/`.no`) without guarding their presence, so a real
 * response that doesn't match the assumed shape throws a `TypeError`
 * rather than failing gracefully — caught here and turned into the same
 * `null`-plus-`console.warn` contract every other boundary in this app
 * uses, rather than an uncaught exception crashing the caller (found by
 * `scripts/verify-live-tickers.ts`'s own test suite feeding it a
 * deliberately wrong shape).
 */
export async function fetchOrderbook(ticker: string): Promise<RawOrderBook | null> {
  const raw = await fetchJson<UnverifiedRawOrderbookResponse>(
    `${KALSHI_BASE_URL}/markets/${encodeURIComponent(ticker)}/orderbook`,
  );
  if (raw === null) {
    return null;
  }
  try {
    return parseRawOrderbook(raw);
  } catch (error) {
    console.warn(
      `[kalshi] Failed to parse orderbook response for ${ticker} — the assumed wire shape may be wrong:`,
      error,
    );
    return null;
  }
}
