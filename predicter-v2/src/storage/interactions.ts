import type { KeyValueStore, TrackedInteraction } from './types';
import { INTERACTIONS_STORAGE_KEY } from './keys';

export function readInteractions(store: KeyValueStore): TrackedInteraction[] {
  const raw = store.getItem(INTERACTIONS_STORAGE_KEY);
  if (raw === null) {
    return [];
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as TrackedInteraction[]) : [];
  } catch {
    return [];
  }
}

/**
 * Unlike the archive, this pre-resolution buffer is mutable: a market
 * being tracked can be re-recorded (e.g. the user edits their thesis
 * before settlement) or removed once it settles and moves into the
 * permanent archive. Re-recording the same (ticker, interactedAt) pair
 * replaces the earlier entry rather than duplicating it.
 */
export function recordInteraction(store: KeyValueStore, interaction: TrackedInteraction): void {
  const current = readInteractions(store);
  const withoutExisting = current.filter(
    (i) => !(i.ticker === interaction.ticker && i.interactedAt === interaction.interactedAt),
  );
  store.setItem(INTERACTIONS_STORAGE_KEY, JSON.stringify([interaction, ...withoutExisting]));
}

export function removeInteraction(store: KeyValueStore, ticker: string, interactedAt: number): void {
  const current = readInteractions(store);
  const filtered = current.filter((i) => !(i.ticker === ticker && i.interactedAt === interactedAt));
  store.setItem(INTERACTIONS_STORAGE_KEY, JSON.stringify(filtered));
}
