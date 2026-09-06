import { afterEach, describe, expect, it, vi } from 'vitest';
import { checkAndArchiveIfSettled } from './settlementSync';
import * as client from './client';
import { readArchive } from '../../storage/archive';
import { readInteractions, recordInteraction } from '../../storage/interactions';
import type { KeyValueStore, TrackedInteraction } from '../../storage/types';

class MemoryStore implements KeyValueStore {
  private readonly data = new Map<string, string>();
  getItem(key: string): string | null {
    return this.data.has(key) ? (this.data.get(key) ?? null) : null;
  }
  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

function interaction(overrides: Partial<TrackedInteraction> = {}): TrackedInteraction {
  return {
    ticker: 'KXFED-25JUN-T5',
    interactedAt: 1000,
    userEstimatePct: 65,
    marketProbabilityPct: 50,
    marketProbabilitySource: 'orderbook-midpoint',
    thesis: 'Test thesis',
    closeTimeMs: 5000,
    ...overrides,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('checkAndArchiveIfSettled', () => {
  it('archives and removes the interaction when the market has genuinely settled', async () => {
    vi.spyOn(client, 'fetchMarket').mockResolvedValue({
      ticker: 'KXFED-25JUN-T5',
      status: 'settled',
      closeTimeMs: 5000,
      result: 'yes',
      yesBidDollars: null,
      yesAskDollars: null,
    });
    const store = new MemoryStore();
    recordInteraction(store, interaction());

    const outcome = await checkAndArchiveIfSettled(store, interaction());

    expect(outcome).toBe('archived');
    expect(readArchive(store)).toHaveLength(1);
    expect(readArchive(store)[0]?.outcome).toBe('yes');
    expect(readInteractions(store)).toHaveLength(0);
  });

  it('does not archive a not-yet-settled market', async () => {
    vi.spyOn(client, 'fetchMarket').mockResolvedValue({
      ticker: 'KXFED-25JUN-T5',
      status: 'open',
      closeTimeMs: 5000,
      result: undefined,
      yesBidDollars: null,
      yesAskDollars: null,
    });
    const store = new MemoryStore();

    const outcome = await checkAndArchiveIfSettled(store, interaction());

    expect(outcome).toBe('not-settled');
    expect(readArchive(store)).toHaveLength(0);
  });

  it('never coerces an unrecognized settled state to a fabricated outcome (handoff Part V item D)', async () => {
    vi.spyOn(client, 'fetchMarket').mockResolvedValue({
      ticker: 'KXFED-25JUN-T5',
      status: 'settled',
      closeTimeMs: 5000,
      result: 'voided',
      yesBidDollars: null,
      yesAskDollars: null,
    });
    const store = new MemoryStore();

    const outcome = await checkAndArchiveIfSettled(store, interaction());

    expect(outcome).toBe('unrecognized');
    expect(readArchive(store)).toHaveLength(0);
  });

  it('reports fetch-failed without archiving when the market cannot be loaded', async () => {
    vi.spyOn(client, 'fetchMarket').mockResolvedValue(null);
    const store = new MemoryStore();

    const outcome = await checkAndArchiveIfSettled(store, interaction());

    expect(outcome).toBe('fetch-failed');
    expect(readArchive(store)).toHaveLength(0);
  });
});
