import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchMarket, fetchOrderbook, KALSHI_BASE_URL } from './client';

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } });
}

describe('fetchMarket', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('requests the confirmed endpoint path and parses the response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        ticker: 'KXFED-25JUN-T5',
        status: 'open',
        close_time: '2030-01-01T00:00:00Z',
        yes_bid_dollars: '0.4',
        yes_ask_dollars: '0.45',
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await fetchMarket('KXFED-25JUN-T5');

    expect(fetchMock).toHaveBeenCalledWith(`${KALSHI_BASE_URL}/markets/KXFED-25JUN-T5`, undefined);
    expect(result?.status).toBe('open');
    expect(result?.yesBidDollars).toBe(0.4);
  });

  it('returns null when the underlying request fails, via the defensive fetch pattern', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('err', { status: 500 })));
    const result = await fetchMarket('X');
    expect(result).toBeNull();
  });
});

describe('fetchOrderbook', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('requests the confirmed orderbook endpoint path and parses the response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ orderbook: { yes: [[10, 5]], no: [[20, 3]] } }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await fetchOrderbook('KXFED-25JUN-T5');

    expect(fetchMock).toHaveBeenCalledWith(`${KALSHI_BASE_URL}/markets/KXFED-25JUN-T5/orderbook`, undefined);
    expect(result).toEqual({
      yesBids: [{ priceCents: 10, sizeContracts: 5 }],
      noBids: [{ priceCents: 20, sizeContracts: 3 }],
    });
  });

  it('returns null when the underlying request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('err', { status: 404 })));
    expect(await fetchOrderbook('X')).toBeNull();
  });

  it('returns null (and warns) rather than throwing when a 200 response does not match the assumed shape', async () => {
    // Regression: parseRawOrderbook reads raw.orderbook.yes/.no without
    // guarding presence, so an unexpected real shape used to throw an
    // uncaught TypeError here instead of failing gracefully - found by
    // scripts/verify-live-tickers.ts's own test suite.
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ yes_side: [], no_side: [] })));

    await expect(fetchOrderbook('X')).resolves.toBeNull();
    expect(warnSpy).toHaveBeenCalledTimes(1);
    warnSpy.mockRestore();
  });
});
