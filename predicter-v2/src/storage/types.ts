import type { Category } from '../domain/category';

/**
 * Minimal key-value interface so every storage function takes its store as
 * an explicit argument rather than reaching for the global `localStorage`.
 * Production wires this to `window.localStorage`; tests wire it to an
 * in-memory fake — so a test run can never read or write the user's real
 * archive, and test fixtures (necessarily synthetic prediction records)
 * can never leak into it or be mistaken for it.
 */
export interface KeyValueStore {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

/**
 * A single permanently-archived, settled market. `orderBookSnapshot` is
 * optional per the handoff's own caveat: some records will have full depth
 * and some will not, and consumers (the future backtest, Stage 6) must
 * branch on its absence explicitly rather than substituting a default.
 * Its concrete shape is defined once Stage 7 wires real Kalshi orderbook
 * data through; `unknown` here is a deliberate placeholder, not a modeling
 * decision.
 */
/**
 * Two distinct probability numbers get stored, not one: the user's own
 * belief (`userEstimatePct`, scored for the user's Brier/log-loss) and the
 * market's fair probability at the moment of logging (`marketProbabilityPct`,
 * scored separately as the baseline comparison the handoff describes —
 * "It also computes the market's log loss alongside the user's"). Collapsing
 * these into one field would make that baseline comparison impossible to
 * reconstruct later. `marketProbabilitySource` preserves the
 * `FairProbability` provenance tag (Stage 3) permanently, so a
 * `'user-typed'` (Theoretical-mode) record stays distinguishable from a
 * real orderbook snapshot for the rest of its life, even after archiving.
 */
export interface ResolvedMarketRecord {
  readonly archiveId: string;
  readonly ticker: string;
  readonly interactedAt: number; // epoch ms — when the prediction was logged
  readonly archivedAt: number; // epoch ms — when this record entered the archive
  readonly category: Category;
  readonly categorySource: 'auto-detected' | 'user-override';
  readonly userEstimatePct: number; // 0-100 — the user's own belief
  readonly marketProbabilityPct: number; // 0-100 — the market's fair probability at log time
  readonly marketProbabilitySource: 'orderbook-midpoint' | 'user-typed';
  readonly thesis: string;
  readonly outcome: 'yes' | 'no';
  readonly closeTimeMs: number;
  readonly orderBookSnapshot?: unknown;
}

/** A prediction being tracked before its market has settled. */
export interface TrackedInteraction {
  readonly ticker: string;
  readonly interactedAt: number;
  readonly userEstimatePct: number;
  readonly marketProbabilityPct: number;
  readonly marketProbabilitySource: 'orderbook-midpoint' | 'user-typed';
  readonly thesis: string;
  readonly closeTimeMs: number;
  readonly categoryOverride?: Category;
}
