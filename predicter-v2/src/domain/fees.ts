import type { Dollars } from './money';
import { roundUpToCent } from './money';

export type OrderRole = 'taker' | 'maker';

/** Verified against Kalshi documentation and a real worked example (handoff Part III). */
export const TAKER_FEE_RATE = 0.07;

/**
 * NOT a stated Kalshi fact. Kalshi's own help center says maker fees apply
 * to "some markets" — conditional, not universally zero. This coefficient
 * is reverse-engineered from a single verified worked example (200
 * contracts @ 49c = $0.88 exactly) and is roughly 1/4 of the taker rate.
 *
 * A prior build tool claimed maker orders "pay 0% fees ($0.00)" — false,
 * caught by independent web verification, and explicitly rejected (handoff
 * Part VII). Any UI surfacing this rate must label it an estimate; never
 * upgrade it to a stated fact, and never display $0.00 as the maker fee.
 */
export const MAKER_FEE_RATE_ESTIMATE = 0.0175;

export interface FeeInput {
  readonly contracts: number;
  readonly priceDollars: Dollars;
  readonly role: OrderRole;
  /** Per-series multiplier (1.0 default; 0.5 for S&P/Nasdaq index series). */
  readonly multiplier?: number;
}

/**
 * fee = roundUp(multiplier * rate * contracts * price * (1 - price))
 *
 * Rounding is always UP to the next whole cent, never to nearest — so
 * scaling by a multiplier does not scale the rounded result proportionally
 * near a cent boundary. That's correct behavior, not a bug (see
 * fees.test.ts for a worked case).
 */
export function computeFee(input: FeeInput): Dollars {
  const { contracts, priceDollars, role, multiplier = 1 } = input;
  const rate = role === 'taker' ? TAKER_FEE_RATE : MAKER_FEE_RATE_ESTIMATE;
  const raw = multiplier * rate * contracts * priceDollars * (1 - priceDollars);
  return roundUpToCent(raw);
}
