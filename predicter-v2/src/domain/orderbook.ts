import type { Dollars } from './money';
import { cents, centsToDollars, dollars, roundUpToCent } from './money';
import type { OrderRole } from './fees';
import { rawFee } from './fees';

export interface OrderBookLevel {
  /** Whole cents, 1-99. */
  readonly priceCents: number;
  readonly sizeContracts: number;
}

/**
 * Shape of what the Kalshi API actually returns: bids only, for both sides,
 * in ascending price order (best bid LAST). See handoff Part III.
 */
export interface RawOrderBook {
  readonly yesBids: readonly OrderBookLevel[];
  readonly noBids: readonly OrderBookLevel[];
}

/**
 * The book after normalization: every side present (asks derived from the
 * opposite side's bids), every array best-first.
 */
export interface CanonicalOrderBook {
  /** Best-first: highest price first. */
  readonly yesBids: readonly OrderBookLevel[];
  /** Best-first: lowest price first. */
  readonly yesAsks: readonly OrderBookLevel[];
  readonly noBids: readonly OrderBookLevel[];
  readonly noAsks: readonly OrderBookLevel[];
}

function complement(levels: readonly OrderBookLevel[]): OrderBookLevel[] {
  return levels.map((level) => ({
    priceCents: 100 - level.priceCents,
    sizeContracts: level.sizeContracts,
  }));
}

/**
 * YES-ask = 1.00 - NO-bid, NO-ask = 1.00 - YES-bid (handoff Part III). The
 * raw arrays are ascending with the best bid last; complementing an
 * ascending array of bid prices produces a *descending* array of ask
 * prices (price and complement move in opposite directions), so the
 * complemented array is reversed to restore best-first order — exactly the
 * sequence the handoff specifies: "derive the complement, arrays are
 * ascending... reverse after complementing."
 */
export function normalizeOrderBook(raw: RawOrderBook): CanonicalOrderBook {
  return {
    yesBids: [...raw.yesBids].reverse(),
    noBids: [...raw.noBids].reverse(),
    yesAsks: complement(raw.noBids).reverse(),
    noAsks: complement(raw.yesBids).reverse(),
  };
}

export interface SimulateBuyInput {
  readonly book: CanonicalOrderBook;
  readonly side: 'yes' | 'no';
  readonly contracts: number;
  readonly role: OrderRole;
  readonly multiplier?: number;
}

export interface SimulateBuyResult {
  readonly requestedContracts: number;
  readonly filledContracts: number;
  /**
   * `false` means the book could not fill the full request — a liquidity
   * trap (handoff Part IV: "the app simulates walking real book depth...
   * rather than assuming the top-of-book price fills the whole order").
   * The other fields below still describe the partial fill that *is*
   * achievable; nothing here is extrapolated or fabricated for the
   * unfillable remainder.
   */
  readonly fullyFilled: boolean;
  /** `null` only when `filledContracts` is 0 — there is no average of nothing. */
  readonly averagePriceDollars: Dollars | null;
  readonly totalCostDollars: Dollars | null;
  readonly feeDollars: Dollars | null;
  readonly levelsWalked: number;
}

/**
 * Walks the book depth level by level for the exact requested contract
 * count. Fees are accumulated as raw (unrounded) per-level amounts and
 * rounded up to the nearest cent exactly once, at the end — never rounded
 * per level and summed (handoff Part IV, Step 3 fix; see orderbook.test.ts
 * for a worked case showing per-level rounding overcharges).
 */
export function simulateBuy(input: SimulateBuyInput): SimulateBuyResult {
  const { book, side, contracts, role, multiplier } = input;
  const asks = side === 'yes' ? book.yesAsks : book.noAsks;

  let remaining = contracts;
  let filled = 0;
  let totalCostDollars = 0;
  let totalRawFee = 0;
  let levelsWalked = 0;

  for (const level of asks) {
    if (remaining <= 0) {
      break;
    }
    const take = Math.min(remaining, level.sizeContracts);
    if (take <= 0) {
      continue;
    }
    const priceDollars = centsToDollars(cents(level.priceCents));
    totalCostDollars += take * priceDollars;
    totalRawFee += rawFee({
      contracts: take,
      priceDollars,
      role,
      ...(multiplier === undefined ? {} : { multiplier }),
    });
    filled += take;
    remaining -= take;
    levelsWalked += 1;
  }

  if (filled === 0) {
    return {
      requestedContracts: contracts,
      filledContracts: 0,
      fullyFilled: contracts <= 0,
      averagePriceDollars: null,
      totalCostDollars: null,
      feeDollars: null,
      levelsWalked: 0,
    };
  }

  return {
    requestedContracts: contracts,
    filledContracts: filled,
    fullyFilled: filled === contracts,
    averagePriceDollars: dollars(totalCostDollars / filled),
    totalCostDollars: dollars(totalCostDollars),
    feeDollars: roundUpToCent(totalRawFee),
    levelsWalked,
  };
}
