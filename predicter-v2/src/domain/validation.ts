/**
 * A prior build let a blank price, 0 contracts, or a 150% probability flow
 * straight through to the Analysis card, which then rendered a confident
 * "+150% edge" — nonsense presented as a real number (handoff Part IV,
 * Phase 1: "Impossible-input validation"). These functions are the
 * structural guard: the UI (Stage 9) must check `valid` before computing or
 * rendering anything downstream, so the Analysis card hides entirely on
 * invalid input rather than rendering a plausible-looking lie.
 */
export type InputValidation = { readonly valid: true } | { readonly valid: false; readonly reason: string };

const VALID: InputValidation = { valid: true };

export function validateProbabilityPct(pct: number): InputValidation {
  if (!Number.isFinite(pct)) {
    return { valid: false, reason: 'Probability must be a number.' };
  }
  if (pct < 0 || pct > 100) {
    return { valid: false, reason: 'Probability must be between 0% and 100%.' };
  }
  return VALID;
}

export function validateContracts(contracts: number): InputValidation {
  if (!Number.isFinite(contracts)) {
    return { valid: false, reason: 'Contracts must be a number.' };
  }
  if (!Number.isInteger(contracts)) {
    return { valid: false, reason: 'Contracts must be a whole number.' };
  }
  if (contracts <= 0) {
    return { valid: false, reason: 'Contracts must be greater than 0.' };
  }
  return VALID;
}

/** `priceDollars` must be a real Kalshi-style price: strictly between $0 and $1. */
export function validatePriceDollars(priceDollars: number): InputValidation {
  if (!Number.isFinite(priceDollars)) {
    return { valid: false, reason: 'Price must be a number.' };
  }
  if (priceDollars <= 0 || priceDollars >= 1) {
    return { valid: false, reason: 'Price must be greater than $0 and less than $1.' };
  }
  return VALID;
}
