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

/** See `schema.ts`'s doc comment on `UnverifiedRawOrderbookResponse` — the wire shape here is unverified. */
export async function fetchOrderbook(ticker: string): Promise<RawOrderBook | null> {
  const raw = await fetchJson<UnverifiedRawOrderbookResponse>(
    `${KALSHI_BASE_URL}/markets/${encodeURIComponent(ticker)}/orderbook`,
  );
  if (raw === null) {
    return null;
  }
  return parseRawOrderbook(raw);
}
