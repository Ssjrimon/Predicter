#!/usr/bin/env -S npx tsx
/**
 * Self-correcting live-verification tool for the Kalshi client
 * (src/data/kalshi/*). Neither this sandbox nor the "trusted network"
 * remote environment tried during this session could reach
 * external-api.kalshi.com (a hard proxy block in one case, a
 * human-confirmation gate this agent can't click through in the other —
 * see PROJECT_STATUS.md's Stage 7/12 notes). This script exists so a
 * human running it from a machine with real internet access — or a
 * future session that genuinely has it — can settle the open question in
 * minutes instead of guessing again.
 *
 * What it does, per ticker:
 *   1. Fetches the RAW JSON directly (bypassing the app's fetchJson, which
 *      discards bodies on failure) so a shape mismatch is visible, not
 *      swallowed.
 *   2. Runs it through the actual, already-tested app functions
 *      (fetchMarket, fetchOrderbook, normalizeOrderBook, simulateBuy,
 *      checkMarketExpiry) to see whether real data actually produces sane
 *      output — not just whether the HTTP call succeeded.
 *   3. Reports concretely which of the two flagged "unverified wire shape"
 *      assumptions (the market-list envelope, the orderbook shape in
 *      schema.ts) held up against real data, and prints the raw JSON for
 *      any that didn't, so fixing schema.ts is a five-minute diff, not
 *      another guess.
 *
 * Usage:
 *   npx tsx scripts/verify-live-tickers.ts                 # 20 random open markets
 *   npx tsx scripts/verify-live-tickers.ts KXFED-25JUN-T5 KXHIGHNY-24JAN01-T60   # specific tickers
 */

import { fetchMarket, fetchOrderbook, KALSHI_BASE_URL } from '../src/data/kalshi/client';
import { normalizeOrderBook, simulateBuy } from '../src/domain/orderbook';
import { checkMarketExpiry } from '../src/domain/expiry';

const TARGET_COUNT = 20;

export interface TickerResult {
  readonly ticker: string;
  readonly summaryOk: boolean;
  readonly summaryIssues: string[];
  readonly orderbookOk: boolean;
  readonly orderbookIssues: string[];
}

async function rawFetch(url: string): Promise<{ status: number; body: unknown; raw: string } | null> {
  try {
    const response = await fetch(url);
    const raw = await response.text();
    let body: unknown = null;
    try {
      body = JSON.parse(raw);
    } catch {
      // leave body null; raw text is still reported
    }
    return { status: response.status, body, raw };
  } catch (error) {
    console.error(`  Raw fetch to ${url} threw:`, error);
    return null;
  }
}

export async function discoverTickers(count: number): Promise<string[]> {
  const url = `${KALSHI_BASE_URL}/markets?status=open&limit=${count}`;
  console.log(`Discovering open markets: GET ${url}`);
  const result = await rawFetch(url);
  if (result === null) {
    console.error('Could not reach the markets-list endpoint at all.');
    return [];
  }
  console.log(`  HTTP ${result.status}`);
  if (result.status !== 200) {
    console.error(`  Non-200 response. Raw body:\n${result.raw.slice(0, 2000)}`);
    return [];
  }

  const body = result.body as Record<string, unknown> | unknown[] | null;
  let candidateMarkets: unknown[] | null = null;
  if (Array.isArray(body)) {
    candidateMarkets = body;
    console.log('  Envelope shape: bare array.');
  } else if (body !== null && Array.isArray((body as Record<string, unknown>)['markets'])) {
    candidateMarkets = (body as Record<string, unknown>)['markets'] as unknown[];
    console.log('  Envelope shape: { markets: [...] } — matches this client\'s assumption.');
  } else {
    console.error('  UNEXPECTED ENVELOPE SHAPE. Neither a bare array nor { markets: [...] }.');
    console.error(`  Raw body (first 2000 chars):\n${result.raw.slice(0, 2000)}`);
    return [];
  }

  const tickers: string[] = [];
  for (const market of candidateMarkets) {
    if (typeof market === 'object' && market !== null && typeof (market as Record<string, unknown>)['ticker'] === 'string') {
      tickers.push((market as Record<string, unknown>)['ticker'] as string);
    }
  }
  console.log(`  Extracted ${tickers.length} ticker(s) from the response.`);
  return tickers.slice(0, count);
}

export async function checkTicker(ticker: string): Promise<TickerResult> {
  const summaryIssues: string[] = [];
  const orderbookIssues: string[] = [];

  const rawSummary = await rawFetch(`${KALSHI_BASE_URL}/markets/${encodeURIComponent(ticker)}`);
  const summary = await fetchMarket(ticker);
  if (rawSummary === null || rawSummary.status !== 200) {
    summaryIssues.push(`raw fetch failed or non-200 (status ${rawSummary?.status ?? 'n/a'})`);
  } else if (summary === null) {
    summaryIssues.push('app\'s fetchMarket() returned null despite a 200 raw response — check fetchJson\'s content-type/parsing assumptions');
    summaryIssues.push(`raw body: ${rawSummary.raw.slice(0, 500)}`);
  } else {
    if (!Number.isFinite(summary.closeTimeMs)) {
      summaryIssues.push(`closeTimeMs did not parse to a finite number from close_time — check the assumed ISO-8601 format`);
    }
    if (summary.yesBidDollars !== null && (summary.yesBidDollars < 0 || summary.yesBidDollars > 1)) {
      summaryIssues.push(`yesBidDollars (${summary.yesBidDollars}) is outside [0,1] — price parsing may be wrong`);
    }
    if (summary.yesAskDollars !== null && (summary.yesAskDollars < 0 || summary.yesAskDollars > 1)) {
      summaryIssues.push(`yesAskDollars (${summary.yesAskDollars}) is outside [0,1] — price parsing may be wrong`);
    }
    const expiry = checkMarketExpiry({ status: summary.status, closeTimeMs: summary.closeTimeMs, nowMs: Date.now() });
    console.log(`  [${ticker}] status=${summary.status} expiry=${expiry.kind} bid=${summary.yesBidDollars} ask=${summary.yesAskDollars}`);
  }

  const rawOrderbook = await rawFetch(`${KALSHI_BASE_URL}/markets/${encodeURIComponent(ticker)}/orderbook`);
  const orderbook = await fetchOrderbook(ticker);
  if (rawOrderbook === null || rawOrderbook.status !== 200) {
    orderbookIssues.push(`raw fetch failed or non-200 (status ${rawOrderbook?.status ?? 'n/a'})`);
  } else if (orderbook === null) {
    orderbookIssues.push('app\'s fetchOrderbook() returned null despite a 200 raw response — the assumed { orderbook: { yes: [...], no: [...] } } shape in schema.ts is likely WRONG');
    orderbookIssues.push(`raw body (first 1000 chars): ${rawOrderbook.raw.slice(0, 1000)}`);
  } else {
    const hasLevels = orderbook.yesBids.length > 0 || orderbook.noBids.length > 0;
    if (!hasLevels) {
      orderbookIssues.push('parsed to an orderbook with zero levels on both sides — could be a genuinely empty book, or a wrong shape silently producing empty arrays; compare against raw body below');
      orderbookIssues.push(`raw body (first 1000 chars): ${rawOrderbook.raw.slice(0, 1000)}`);
    } else {
      const badPrice = [...orderbook.yesBids, ...orderbook.noBids].find((l) => l.priceCents < 1 || l.priceCents > 99);
      if (badPrice !== undefined) {
        orderbookIssues.push(`found a level with priceCents=${badPrice.priceCents}, outside [1,99] — price/cents parsing may be wrong`);
      }
      try {
        const canonical = normalizeOrderBook(orderbook);
        const sim = simulateBuy({ book: canonical, side: 'yes', contracts: 10, role: 'taker' });
        console.log(`  [${ticker}] orderbook OK — ${orderbook.yesBids.length} yes bids, ${orderbook.noBids.length} no bids, sample fill=${sim.filledContracts}/10`);
      } catch (error) {
        orderbookIssues.push(`normalizeOrderBook/simulateBuy threw on real data: ${String(error)}`);
      }
    }
  }

  return {
    ticker,
    summaryOk: summaryIssues.length === 0,
    summaryIssues,
    orderbookOk: orderbookIssues.length === 0,
    orderbookIssues,
  };
}

async function main(): Promise<void> {
  const explicitTickers = process.argv.slice(2);
  const tickers = explicitTickers.length > 0 ? explicitTickers : await discoverTickers(TARGET_COUNT);

  if (tickers.length === 0) {
    console.error('\nNo tickers to check. If discovery failed, pass tickers explicitly:');
    console.error('  npx tsx scripts/verify-live-tickers.ts TICKER1 TICKER2 ...');
    process.exitCode = 1;
    return;
  }

  console.log(`\nChecking ${tickers.length} ticker(s)...\n`);
  const results: TickerResult[] = [];
  for (const ticker of tickers) {
    results.push(await checkTicker(ticker));
  }

  const summaryOkCount = results.filter((r) => r.summaryOk).length;
  const orderbookOkCount = results.filter((r) => r.orderbookOk).length;

  console.log(`\n=== SUMMARY ===`);
  console.log(`Market summary parsed cleanly: ${summaryOkCount}/${results.length}`);
  console.log(`Orderbook parsed cleanly:      ${orderbookOkCount}/${results.length}`);

  const problems = results.filter((r) => !r.summaryOk || !r.orderbookOk);
  if (problems.length > 0) {
    console.log(`\n=== ISSUES FOUND (fix schema.ts based on these) ===`);
    for (const r of problems) {
      console.log(`\n${r.ticker}:`);
      for (const issue of r.summaryIssues) console.log(`  [summary] ${issue}`);
      for (const issue of r.orderbookIssues) console.log(`  [orderbook] ${issue}`);
    }
    process.exitCode = 1;
  } else {
    console.log('\nAll checks passed. The schema.ts assumptions match real Kalshi responses for these tickers.');
  }
}

// Only run when executed directly (`tsx scripts/verify-live-tickers.ts`), not
// when imported by verify-live-tickers.test.ts.
const isMainModule = process.argv[1] !== undefined && import.meta.url === new URL(process.argv[1], 'file://').href;
if (isMainModule) {
  void main();
}
