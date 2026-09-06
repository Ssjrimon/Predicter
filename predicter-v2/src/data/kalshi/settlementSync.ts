import { fetchMarket } from './client';
import { extractSettledOutcome } from '../../storage/settlement';
import { appendResolvedMarket } from '../../storage/archive';
import { removeInteraction } from '../../storage/interactions';
import { assignCategory } from '../../domain/category';
import type { KeyValueStore, TrackedInteraction } from '../../storage/types';

export type SyncOutcome = 'archived' | 'not-settled' | 'unrecognized' | 'fetch-failed';

/**
 * Checks one tracked (pre-resolution) interaction against Kalshi's current
 * market state and archives it if — and only if — the settlement guard
 * (handoff Part V items C/D) accepts the result. The outcome is sourced
 * strictly from Kalshi's own `result` field; there is no path here that
 * lets a user mark a prediction resolved by hand.
 */
export async function checkAndArchiveIfSettled(
  store: KeyValueStore,
  interaction: TrackedInteraction,
): Promise<SyncOutcome> {
  const summary = await fetchMarket(interaction.ticker);
  if (summary === null) {
    return 'fetch-failed';
  }

  const outcome = extractSettledOutcome(summary.status, summary.result);
  if (outcome === null) {
    // extractSettledOutcome already warns on a genuinely unrecognized
    // state; a simply-not-yet-settled market warns nothing, and both
    // return null here, so distinguish them for the caller by re-checking
    // status directly rather than re-deriving the warning.
    return summary.status === 'settled' ? 'unrecognized' : 'not-settled';
  }

  const category = assignCategory(interaction.ticker, interaction.categoryOverride);
  const archived = appendResolvedMarket(store, {
    archiveId: `${interaction.ticker}-${interaction.interactedAt}`,
    ticker: interaction.ticker,
    interactedAt: interaction.interactedAt,
    archivedAt: Date.now(),
    category: category.category,
    categorySource: category.source,
    userEstimatePct: interaction.userEstimatePct,
    marketProbabilityPct: interaction.marketProbabilityPct,
    marketProbabilitySource: interaction.marketProbabilitySource,
    thesis: interaction.thesis,
    outcome,
    closeTimeMs: interaction.closeTimeMs,
  });

  if (archived) {
    removeInteraction(store, interaction.ticker, interaction.interactedAt);
  }
  return 'archived';
}
