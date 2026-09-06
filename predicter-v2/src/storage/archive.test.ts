import { describe, expect, it } from 'vitest';
import * as archiveModule from './archive';
import { appendResolvedMarket, exportArchiveCsv, exportArchiveJson, readArchive } from './archive';
import { ARCHIVE_STORAGE_KEY } from './keys';
import type { KeyValueStore, ResolvedMarketRecord } from './types';

class MemoryStore implements KeyValueStore {
  private readonly data = new Map<string, string>();
  getItem(key: string): string | null {
    return this.data.has(key) ? (this.data.get(key) ?? null) : null;
  }
  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

function record(overrides: Partial<ResolvedMarketRecord> = {}): ResolvedMarketRecord {
  return {
    archiveId: 'a1',
    ticker: 'KXFED-25JUN-T5',
    interactedAt: 1000,
    archivedAt: 2000,
    category: 'Fed',
    categorySource: 'auto-detected',
    predictedProbabilityPct: 60,
    thesis: 'Test thesis',
    outcome: 'yes',
    closeTimeMs: 1500,
    ...overrides,
  };
}

describe('readArchive', () => {
  it('returns an empty array when nothing has been written', () => {
    expect(readArchive(new MemoryStore())).toEqual([]);
  });

  it('returns an empty array rather than throwing on malformed JSON', () => {
    const store = new MemoryStore();
    store.setItem(ARCHIVE_STORAGE_KEY, 'not json');
    expect(() => readArchive(store)).not.toThrow();
    expect(readArchive(store)).toEqual([]);
  });
});

describe('appendResolvedMarket', () => {
  it('appends a new record and returns true', () => {
    const store = new MemoryStore();
    const ok = appendResolvedMarket(store, record());
    expect(ok).toBe(true);
    expect(readArchive(store)).toHaveLength(1);
  });

  it('is a pure prepend - newest record first', () => {
    const store = new MemoryStore();
    appendResolvedMarket(store, record({ archiveId: 'a1' }));
    appendResolvedMarket(store, record({ archiveId: 'a2', ticker: 'KXFED-25JUL-T5' }));
    const archive = readArchive(store);
    expect(archive.map((r) => r.archiveId)).toEqual(['a2', 'a1']);
  });

  it('refuses a duplicate archiveId and returns false', () => {
    const store = new MemoryStore();
    appendResolvedMarket(store, record({ archiveId: 'dup' }));
    const ok = appendResolvedMarket(store, record({ archiveId: 'dup', ticker: 'different-ticker' }));
    expect(ok).toBe(false);
    expect(readArchive(store)).toHaveLength(1);
  });

  it('refuses a duplicate ticker+interactedAt pair even with a different archiveId', () => {
    const store = new MemoryStore();
    appendResolvedMarket(store, record({ archiveId: 'a1', ticker: 'X', interactedAt: 500 }));
    const ok = appendResolvedMarket(store, record({ archiveId: 'a2', ticker: 'X', interactedAt: 500 }));
    expect(ok).toBe(false);
    expect(readArchive(store)).toHaveLength(1);
  });

  it("exposes no update or delete function - the module's only mutation is this one append", () => {
    // Structural check, not behavioral: the module's exported surface is
    // exactly what append-only requires, nothing more.
    expect(Object.keys(archiveModule).sort()).toEqual([
      'appendResolvedMarket',
      'exportArchiveCsv',
      'exportArchiveJson',
      'readArchive',
    ]);
  });
});

describe('exportArchiveJson / exportArchiveCsv', () => {
  it('exports valid JSON that round-trips', () => {
    const store = new MemoryStore();
    appendResolvedMarket(store, record());
    const json = exportArchiveJson(store);
    expect(JSON.parse(json)).toHaveLength(1);
  });

  it('exports an empty string for CSV when the archive is empty', () => {
    expect(exportArchiveCsv(new MemoryStore())).toBe('');
  });

  it('exports a header row plus one row per record', () => {
    const store = new MemoryStore();
    appendResolvedMarket(store, record({ archiveId: 'a1' }));
    appendResolvedMarket(store, record({ archiveId: 'a2', ticker: 'other' }));
    const csv = exportArchiveCsv(store);
    const lines = csv.split('\n');
    expect(lines).toHaveLength(3); // header + 2 rows
    expect(lines[0]).toContain('archiveId');
  });
});
