/**
 * Branded money types. `Cents` and `Dollars` are structurally `number` but
 * nominally distinct, so passing a cents value where a fee formula expects
 * dollars (or vice versa) is a compile error rather than a silent unit bug.
 */
export type Cents = number & { readonly __brand: 'Cents' };
export type Dollars = number & { readonly __brand: 'Dollars' };

export function dollars(value: number): Dollars {
  return value as Dollars;
}

export function cents(value: number): Cents {
  return value as Cents;
}

export function dollarsToCents(value: Dollars): Cents {
  return Math.round(value * 100) as Cents;
}

export function centsToDollars(value: Cents): Dollars {
  return (value / 100) as Dollars;
}

/**
 * IEEE 754 can push a product a fraction above an exact cent boundary before
 * rounding — e.g. `0.07 * 100 * 0.5 * 0.5` lands microscopically above 1.75,
 * so a naive `Math.ceil(raw * 100) / 100` returns $1.76 instead of $1.75
 * (verified handoff Part III / Part IV Phase 1). This subtracts a tolerance
 * tighter than any real fee input can produce before applying the ceiling,
 * so genuine fractional cents still round up correctly.
 */
const ROUNDING_EPSILON = 1e-8;

export function roundUpToCent(rawDollars: number): Dollars {
  return (Math.ceil(rawDollars * 100 - ROUNDING_EPSILON) / 100) as Dollars;
}
