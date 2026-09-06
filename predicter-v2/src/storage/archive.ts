import type { KeyValueStore, ResolvedMarketRecord } from './types';
import { ARCHIVE_STORAGE_KEY } from './keys';

export function readArchive(store: KeyValueStore): ResolvedMarketRecord[] {
  const raw = store.getItem(ARCHIVE_STORAGE_KEY);
  if (raw === null) {
    return [];
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as ResolvedMarketRecord[]) : [];
  } catch {
    return [];
  }
}

function isDuplicate(existing: readonly ResolvedMarketRecord[], record: ResolvedMarketRecord): boolean {
  return existing.some(
    (r) => r.archiveId === record.archiveId || (r.ticker === record.ticker && r.interactedAt === record.interactedAt),
  );
}

/**
 * Genuinely append-only. Dedupes by `archiveId` OR `ticker + interactedAt`
 * and returns `false` if the record already exists. The only write is
 * `[record, ...current]` — a pure prepend. There is no update or delete
 * function anywhere in this module: nothing exists to call by accident, or
 * for a future agent to be tempted into adding "just this once"
 * (handoff Step 5).
 */
export function appendResolvedMarket(store: KeyValueStore, record: ResolvedMarketRecord): boolean {
  const current = readArchive(store);
  if (isDuplicate(current, record)) {
    return false;
  }
  store.setItem(ARCHIVE_STORAGE_KEY, JSON.stringify([record, ...current]));
  return true;
}

export function exportArchiveJson(store: KeyValueStore): string {
  return JSON.stringify(readArchive(store), null, 2);
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function exportArchiveCsv(store: KeyValueStore): string {
  const records = readArchive(store);
  const [first] = records;
  if (first === undefined) {
    return '';
  }
  const headers = Object.keys(first);
  const rows = records.map((record) => {
    const asRecord = record as unknown as Record<string, unknown>;
    return headers.map((header) => csvEscape(String(asRecord[header] ?? ''))).join(',');
  });
  return [headers.join(','), ...rows].join('\n');
}
