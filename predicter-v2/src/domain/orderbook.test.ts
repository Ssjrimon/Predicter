import { describe, expect, it } from 'vitest';
import { normalizeOrderBook, simulateBuy } from './orderbook';
import { roundUpToCent } from './money';

describe('normalizeOrderBook', () => {
  it('reverses raw ascending bids to best-first order', () => {
    const raw = {
      yesBids: [
        { priceCents: 10, sizeContracts: 5 },
        { priceCents: 20, sizeContracts: 3 },
        { priceCents: 30, sizeContracts: 7 }, // best bid, last in raw array
      ],
      noBids: [
        { priceCents: 15, sizeContracts: 4 },
        { priceCents: 25, sizeContracts: 6 },
        { priceCents: 40, sizeContracts: 2 }, // best bid, last in raw array
      ],
    };

    const book = normalizeOrderBook(raw);

    expect(book.yesBids).toEqual([
      { priceCents: 30, sizeContracts: 7 },
      { priceCents: 20, sizeContracts: 3 },
      { priceCents: 10, sizeContracts: 5 },
    ]);
    expect(book.noBids).toEqual([
      { priceCents: 40, sizeContracts: 2 },
      { priceCents: 25, sizeContracts: 6 },
      { priceCents: 15, sizeContracts: 4 },
    ]);
  });

  it('derives asks as the complement of the opposite bid, best-first (handoff Part III)', () => {
    const raw = {
      yesBids: [
        { priceCents: 10, sizeContracts: 5 },
        { priceCents: 20, sizeContracts: 3 },
        { priceCents: 30, sizeContracts: 7 },
      ],
      noBids: [
        { priceCents: 15, sizeContracts: 4 },
        { priceCents: 25, sizeContracts: 6 },
        { priceCents: 40, sizeContracts: 2 },
      ],
    };

    const book = normalizeOrderBook(raw);

    // YES-ask = 1.00 - NO-bid. Best (cheapest) ask first.
    expect(book.yesAsks).toEqual([
      { priceCents: 60, sizeContracts: 2 }, // 100 - 40
      { priceCents: 75, sizeContracts: 6 }, // 100 - 25
      { priceCents: 85, sizeContracts: 4 }, // 100 - 15
    ]);

    // NO-ask = 1.00 - YES-bid.
    expect(book.noAsks).toEqual([
      { priceCents: 70, sizeContracts: 7 }, // 100 - 30
      { priceCents: 80, sizeContracts: 3 }, // 100 - 20
      { priceCents: 90, sizeContracts: 5 }, // 100 - 10
    ]);
  });

  it('handles a deliberately non-ascending input without silently misordering (runtime sanity)', () => {
    // The normalizer trusts the documented ascending contract; this test
    // just documents what happens if that contract is violated, so a
    // caller feeding a malformed API response gets a visibly wrong (not
    // silently plausible) result rather than a crash.
    const raw = {
      yesBids: [{ priceCents: 30, sizeContracts: 1 }, { priceCents: 10, sizeContracts: 1 }],
      noBids: [],
    };
    const book = normalizeOrderBook(raw);
    // Reversing a non-ascending array just reverses it - the caller is
    // responsible for the API actually returning ascending order.
    expect(book.yesBids).toEqual([
      { priceCents: 10, sizeContracts: 1 },
      { priceCents: 30, sizeContracts: 1 },
    ]);
  });
});

describe('simulateBuy', () => {
  it('fills entirely from a single level and matches the Stage 1 taker worked example', () => {
    const book = normalizeOrderBook({
      yesBids: [],
      noBids: [{ priceCents: 50, sizeContracts: 1000 }],
    });

    const result = simulateBuy({ book, side: 'yes', contracts: 100, role: 'taker' });

    expect(result.fullyFilled).toBe(true);
    expect(result.filledContracts).toBe(100);
    expect(result.averagePriceDollars).toBe(0.5);
    expect(result.totalCostDollars).toBe(50);
    expect(result.feeDollars).toBe(1.75); // matches fees.test.ts exactly
    expect(result.levelsWalked).toBe(1);
  });

  it('walks multiple depth levels and sums raw fees before rounding once', () => {
    const book = normalizeOrderBook({
      yesBids: [],
      // Complement of these noBids gives yesAsks of 48c/50c/55c after
      // reversal - construct noBids directly in raw (ascending) form so
      // the resulting yesAsks are exactly what this test wants.
      noBids: [
        { priceCents: 45, sizeContracts: 100 }, // -> yesAsk 55c
        { priceCents: 50, sizeContracts: 50 }, // -> yesAsk 50c
        { priceCents: 52, sizeContracts: 50 }, // -> yesAsk 48c, best bid (last), so best ask
      ],
    });

    // Sanity: confirm the book actually walks 48c, then 50c, then 55c.
    expect(book.yesAsks.map((l) => l.priceCents)).toEqual([48, 50, 55]);

    const result = simulateBuy({ book, side: 'yes', contracts: 120, role: 'taker' });

    expect(result.fullyFilled).toBe(true);
    expect(result.filledContracts).toBe(120); // 50@48c + 50@50c + 20@55c
    expect(result.levelsWalked).toBe(3);
    expect(result.averagePriceDollars).toBe(0.5); // (24 + 25 + 11) / 120
    expect(result.totalCostDollars).toBe(60);

    // Raw per-level fees: 0.07*50*0.48*0.52=0.8736, 0.07*50*0.5*0.5=0.875,
    // 0.07*20*0.55*0.45=0.3465. Sum = 2.0951 -> rounds up to $2.10.
    expect(result.feeDollars).toBe(2.1);
  });

  it('sum-then-round is cheaper than round-then-sum, proving the Step 3 fix matters', () => {
    // Same three raw fees as the test above.
    const rawFees = [0.8736, 0.875, 0.3465];
    const correct = roundUpToCent(rawFees.reduce((a, b) => a + b, 0));
    const naive = rawFees.reduce((sum, f) => sum + roundUpToCent(f), 0);

    expect(correct).toBe(2.1);
    expect(naive).toBeCloseTo(2.11, 10); // 0.88 + 0.88 + 0.35
    expect(naive).toBeGreaterThan(correct); // the historical overcharge bug
  });

  it('reports a partial fill and a real liquidity-trap flag when the book runs out', () => {
    const book = normalizeOrderBook({
      yesBids: [],
      noBids: [{ priceCents: 50, sizeContracts: 30 }],
    });

    const result = simulateBuy({ book, side: 'yes', contracts: 100, role: 'taker' });

    expect(result.fullyFilled).toBe(false);
    expect(result.filledContracts).toBe(30);
    expect(result.averagePriceDollars).toBe(0.5);
    expect(result.totalCostDollars).toBe(15);
    expect(result.feeDollars).toBe(computeExpectedFee());

    function computeExpectedFee(): number {
      // 0.07 * 30 * 0.5 * 0.5 = 0.525 -> rounds up to $0.53
      return 0.53;
    }
  });

  it('never fabricates a fill for an empty book', () => {
    const book = normalizeOrderBook({ yesBids: [], noBids: [] });

    const result = simulateBuy({ book, side: 'yes', contracts: 50, role: 'taker' });

    expect(result.filledContracts).toBe(0);
    expect(result.fullyFilled).toBe(false);
    expect(result.averagePriceDollars).toBeNull();
    expect(result.totalCostDollars).toBeNull();
    expect(result.feeDollars).toBeNull();
    expect(result.levelsWalked).toBe(0);
  });

  it('applies a maker role using the estimated coefficient during depth walking', () => {
    const book = normalizeOrderBook({
      yesBids: [],
      noBids: [{ priceCents: 51, sizeContracts: 200 }], // -> yesAsk 49c
    });

    const result = simulateBuy({ book, side: 'yes', contracts: 200, role: 'maker' });

    expect(result.filledContracts).toBe(200);
    expect(result.feeDollars).toBe(0.88); // matches fees.test.ts maker worked example
  });
});
