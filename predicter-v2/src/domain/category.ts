export type Category = 'Fed' | 'Weather' | 'Index' | 'Other';

export interface CategoryAssignment {
  readonly category: Category;
  readonly source: 'auto-detected' | 'user-override';
}

/**
 * Deterministic prefix detection, not a fuzzy guess — checkable by
 * construction (handoff Part IV, Step 4). Only prefixes the handoff
 * actually names are mapped explicitly: `KXFED` and `KXHIGHNY` (Fed and
 * weather markets respectively) and `INX` (index). `KXHIGH` is matched as
 * a prefix rather than the exact `KXHIGHNY` string, on the inference that
 * other city high-temperature series share the same series-ticker
 * convention (handoff Part III: tickers encode series+date+threshold) —
 * this inference is NOT independently verified per other city, unlike
 * `KXHIGHNY` and `KXFED` themselves. Anything unrecognized falls through
 * to 'Other' rather than a guessed category. This is exactly why the
 * override exists: auto-detection is a checkable heuristic, not a fact.
 */
function detectCategoryFromTicker(ticker: string): Category {
  const upper = ticker.toUpperCase();
  if (upper.startsWith('KXFED')) {
    return 'Fed';
  }
  if (upper.startsWith('KXHIGH')) {
    return 'Weather';
  }
  if (upper.startsWith('INX')) {
    return 'Index';
  }
  return 'Other';
}

/**
 * `override`, when present, always wins — auto-detection never overrules
 * an explicit user choice. Per the handoff, this must be read once at
 * archive-record construction time and never re-applied afterward (Stage
 * 5's archive enforces that by having no update path at all, not by this
 * function refusing to be called twice).
 */
export function assignCategory(ticker: string, override?: Category): CategoryAssignment {
  if (override !== undefined) {
    return { category: override, source: 'user-override' };
  }
  return { category: detectCategoryFromTicker(ticker), source: 'auto-detected' };
}
