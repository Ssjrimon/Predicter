import { afterEach, describe, expect, it, vi } from 'vitest';
import { checkTicker, discoverTickers } from './verify-live-tickers';
import { KALSHI_BASE_URL } from '../src/data/kalshi/client';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('discoverTickers', () => {
  it('extracts tickers from the assumed { markets: [...] } envelope', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ markets: [{ ticker: 'A' }, { ticker: 'B' }] })),
    );
    expect(await discoverTickers(20)).toEqual(['A', 'B']);
  });

  it('extracts tickers from a bare-array envelope too', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse([{ ticker: 'A' }, { ticker: 'B' }])));
    expect(await discoverTickers(20)).toEqual(['A', 'B']);
  });

  it('reports an empty list (not a crash) for a genuinely unexpected envelope shape', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ somethingElse: true })));
    expect(await discoverTickers(20)).toEqual([]);
  });
});

describe('checkTicker', () => {
  it('reports success when both endpoints match the assumed shapes', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/orderbook')) {
        return Promise.resolve(jsonResponse({ orderbook: { yes: [[50, 10]], no: [[45, 5]] } }));
      }
      return Promise.resolve(
        jsonResponse({
          ticker: 'X',
          status: 'open',
          close_time: '2030-01-01T00:00:00Z',
          yes_bid_dollars: '0.48',
          yes_ask_dollars: '0.52',
        }),
      );
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await checkTicker('X');
    expect(result.summaryOk).toBe(true);
    expect(result.orderbookOk).toBe(true);
  });

  it('flags a wrong orderbook shape as a real, actionable issue rather than passing silently', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/orderbook')) {
        // A deliberately WRONG shape - not the assumed { orderbook: {...} }.
        return Promise.resolve(jsonResponse({ yes_side: [], no_side: [] }));
      }
      return Promise.resolve(
        jsonResponse({
          ticker: 'X',
          status: 'open',
          close_time: '2030-01-01T00:00:00Z',
          yes_bid_dollars: '0.48',
          yes_ask_dollars: '0.52',
        }),
      );
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await checkTicker('X');
    // fetchOrderbook doesn't throw on this - it "succeeds" with empty
    // arrays (schema.ts's parseRawOrderbook reads .orderbook.yes/.no,
    // which are undefined on this wrong shape, and .map on undefined
    // would throw - let's confirm what actually happens is surfaced,
    // not swallowed).
    expect(result.orderbookOk).toBe(false);
    expect(result.orderbookIssues.length).toBeGreaterThan(0);
  });

  it('flags an out-of-range price as an actionable parsing issue', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/orderbook')) {
        return Promise.resolve(jsonResponse({ orderbook: { yes: [[50, 10]], no: [[45, 5]] } }));
      }
      return Promise.resolve(
        jsonResponse({
          ticker: 'X',
          status: 'open',
          close_time: '2030-01-01T00:00:00Z',
          yes_bid_dollars: '48', // wrong: whole dollars instead of a 0-1 fraction
          yes_ask_dollars: '0.52',
        }),
      );
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await checkTicker('X');
    expect(result.summaryOk).toBe(false);
    expect(result.summaryIssues.some((i) => i.includes('yesBidDollars'))).toBe(true);
  });

  it('reports fetch failures as issues rather than throwing', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('err', { status: 500 })));
    const result = await checkTicker('X');
    expect(result.summaryOk).toBe(false);
    expect(result.orderbookOk).toBe(false);
  });

  it('constructs the expected real endpoint URLs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('err', { status: 500 }));
    vi.stubGlobal('fetch', fetchMock);
    await checkTicker('KXFED-25JUN-T5');
    const calledUrls = fetchMock.mock.calls.map((c) => c[0] as string);
    expect(calledUrls).toContain(`${KALSHI_BASE_URL}/markets/KXFED-25JUN-T5`);
    expect(calledUrls).toContain(`${KALSHI_BASE_URL}/markets/KXFED-25JUN-T5/orderbook`);
  });
});
