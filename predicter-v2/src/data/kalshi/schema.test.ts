import { describe, expect, it } from 'vitest';
import { parseDollarsString, parseMarketSummary, parseRawOrderbook } from './schema';
import type { RawMarketSummary, UnverifiedRawOrderbookResponse } from './schema';

describe('parseDollarsString', () => {
  it('parses a valid decimal string (handoff Part III: prices are string decimals, not numbers)', () => {
    expect(parseDollarsString('0.50')).toBe(0.5);
    expect(parseDollarsString('0.49')).toBe(0.49);
  });

  it('returns null for a non-numeric string rather than NaN flowing downstream', () => {
    expect(parseDollarsString('not-a-price')).toBeNull();
    expect(parseDollarsString('')).toBeNull();
  });
});

describe('parseMarketSummary', () => {
  it('parses confirmed field names into typed values', () => {
    const raw: RawMarketSummary = {
      ticker: 'KXHIGHNY-24JAN01-T60',
      status: 'settled',
      close_time: '2024-01-01T00:00:00Z',
      result: 'yes',
      yes_bid_dollars: '0.48',
      yes_ask_dollars: '0.52',
    };
    const parsed = parseMarketSummary(raw);
    expect(parsed.ticker).toBe('KXHIGHNY-24JAN01-T60');
    expect(parsed.status).toBe('settled');
    expect(parsed.closeTimeMs).toBe(Date.UTC(2024, 0, 1));
    expect(parsed.result).toBe('yes');
    expect(parsed.yesBidDollars).toBe(0.48);
    expect(parsed.yesAskDollars).toBe(0.52);
  });

  it('preserves an absent result as undefined - never coerced', () => {
    const raw: RawMarketSummary = {
      ticker: 'X',
      status: 'open',
      close_time: '2030-01-01T00:00:00Z',
      yes_bid_dollars: '0.5',
      yes_ask_dollars: '0.5',
    };
    expect(parseMarketSummary(raw).result).toBeUndefined();
  });

  it('preserves an invalid price string as null rather than NaN', () => {
    const raw: RawMarketSummary = {
      ticker: 'X',
      status: 'open',
      close_time: '2030-01-01T00:00:00Z',
      yes_bid_dollars: 'garbage',
      yes_ask_dollars: '0.5',
    };
    expect(parseMarketSummary(raw).yesBidDollars).toBeNull();
  });
});

describe('parseRawOrderbook', () => {
  it('translates the placeholder tuple-array wire shape into the domain RawOrderBook shape', () => {
    const raw: UnverifiedRawOrderbookResponse = {
      orderbook: {
        yes: [
          [10, 5],
          [20, 3],
        ],
        no: [[15, 4]],
      },
    };
    expect(parseRawOrderbook(raw)).toEqual({
      yesBids: [
        { priceCents: 10, sizeContracts: 5 },
        { priceCents: 20, sizeContracts: 3 },
      ],
      noBids: [{ priceCents: 15, sizeContracts: 4 }],
    });
  });
});
