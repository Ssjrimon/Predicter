import { describe, expect, it } from 'vitest';
import { readInteractions, recordInteraction, removeInteraction } from './interactions';
import type { KeyValueStore, TrackedInteraction } from './types';

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
    predictedProbabilityPct: 55,
    thesis: 'Test thesis',
    closeTimeMs: 5000,
    ...overrides,
  };
}

describe('readInteractions', () => {
  it('returns an empty array when nothing has been recorded', () => {
    expect(readInteractions(new MemoryStore())).toEqual([]);
  });
});

describe('recordInteraction', () => {
  it('records a new interaction', () => {
    const store = new MemoryStore();
    recordInteraction(store, interaction());
    expect(readInteractions(store)).toHaveLength(1);
  });

  it('replaces an existing entry for the same ticker+interactedAt rather than duplicating it', () => {
    const store = new MemoryStore();
    recordInteraction(store, interaction({ thesis: 'first draft' }));
    recordInteraction(store, interaction({ thesis: 'revised thesis' }));
    const all = readInteractions(store);
    expect(all).toHaveLength(1);
    expect(all[0]?.thesis).toBe('revised thesis');
  });
});

describe('removeInteraction', () => {
  it('removes a tracked interaction once it has settled and moved to the archive', () => {
    const store = new MemoryStore();
    recordInteraction(store, interaction({ ticker: 'A', interactedAt: 1 }));
    recordInteraction(store, interaction({ ticker: 'B', interactedAt: 2 }));
    removeInteraction(store, 'A', 1);
    const remaining = readInteractions(store);
    expect(remaining).toHaveLength(1);
    expect(remaining[0]?.ticker).toBe('B');
  });

  it('is a no-op when the interaction does not exist', () => {
    const store = new MemoryStore();
    recordInteraction(store, interaction());
    expect(() => removeInteraction(store, 'nonexistent', 999)).not.toThrow();
    expect(readInteractions(store)).toHaveLength(1);
  });
});
