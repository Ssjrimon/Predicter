import type { Dollars } from '../../domain/money';
import { dollars } from '../../domain/money';
import type { RawOrderBook } from '../../domain/orderbook';

/**
 * Kalshi's JSON fields (`yes_bid_dollars`, `yes_ask_dollars`, etc.) are
 * string decimals, not numbers (handoff Part III, confirmed). Parsing
 * happens exactly once, at this boundary — nothing downstream ever sees a
 * raw string price.
 */
export function parseDollarsString(raw: string): Dollars | null {
  const value = Number.parseFloat(raw);
  if (!Number.isFinite(value)) {
    return null;
  }
  return dollars(value);
}

/**
 * Market summary fields the handoff confirms exist on Kalshi's market
 * objects (Part III): ticker, status, close_time, expiration_time,
 * result, and the string-decimal price fields. The exact JSON envelope —
 * is this the whole response body, or nested under a `market` key? — is
 * NOT independently confirmed this session: this session's outbound
 * network policy blocks `external-api.kalshi.com` (a real 403 from the
 * proxy's own CONNECT tunnel, confirmed via its status endpoint — not
 * assumed). Verify this shape against a live response before trusting it
 * in production, per the same discipline the handoff applies to its own
 * Part VIII unverified claims.
 */
export interface RawMarketSummary {
  readonly ticker: string;
  readonly status: string;
  readonly close_time: string;
  readonly expiration_time?: string;
  readonly result?: string | null;
  readonly yes_bid_dollars: string;
  readonly yes_ask_dollars: string;
  readonly volume_fp?: string;
}

export interface ParsedMarketSummary {
  readonly ticker: string;
  readonly status: string;
  readonly closeTimeMs: number;
  readonly result: string | null | undefined;
  readonly yesBidDollars: Dollars | null;
  readonly yesAskDollars: Dollars | null;
}

export function parseMarketSummary(raw: RawMarketSummary): ParsedMarketSummary {
  return {
    ticker: raw.ticker,
    status: raw.status,
    closeTimeMs: Date.parse(raw.close_time),
    result: raw.result,
    yesBidDollars: parseDollarsString(raw.yes_bid_dollars),
    yesAskDollars: parseDollarsString(raw.yes_ask_dollars),
  };
}

/**
 * UNVERIFIED WIRE SHAPE. Kalshi's real `/markets/{ticker}/orderbook`
 * response was not checked against a live call this session (see the
 * module doc comment above — network policy blocks the host). This is a
 * best-effort placeholder for a price/size-tuple-array shape. Replace it
 * the moment a live response can be inspected, and update
 * `parseRawOrderbook` to match. The domain layer (Stage 2's
 * `normalizeOrderBook`) is unaffected either way — this function's only
 * job is translating whatever Kalshi actually returns into the domain's
 * clean, already-verified `RawOrderBook` shape, so correcting this one
 * function is the entire blast radius of being wrong here.
 */
export interface UnverifiedRawOrderbookResponse {
  readonly orderbook: {
    readonly yes: ReadonlyArray<readonly [priceCents: number, sizeContracts: number]>;
    readonly no: ReadonlyArray<readonly [priceCents: number, sizeContracts: number]>;
  };
}

export function parseRawOrderbook(raw: UnverifiedRawOrderbookResponse): RawOrderBook {
  return {
    yesBids: raw.orderbook.yes.map(([priceCents, sizeContracts]) => ({ priceCents, sizeContracts })),
    noBids: raw.orderbook.no.map(([priceCents, sizeContracts]) => ({ priceCents, sizeContracts })),
  };
}
