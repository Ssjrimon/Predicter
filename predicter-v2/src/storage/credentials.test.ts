import { describe, expect, it } from 'vitest';
import { clearCredentials, readCredentials, writeCredentials } from './credentials';
import type { KeyValueStore } from './types';

class MemoryStore implements KeyValueStore {
  private readonly data = new Map<string, string>();
  getItem(key: string): string | null {
    return this.data.has(key) ? (this.data.get(key) ?? null) : null;
  }
  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

describe('credentials storage', () => {
  it('returns null when nothing is stored', () => {
    expect(readCredentials(new MemoryStore())).toBeNull();
  });

  it('round-trips a written credential', () => {
    const store = new MemoryStore();
    writeCredentials(store, { apiKeyId: 'key-1', privateKeyPem: '-----BEGIN...-----' });
    expect(readCredentials(store)).toEqual({ apiKeyId: 'key-1', privateKeyPem: '-----BEGIN...-----' });
  });

  it('clears a stored credential', () => {
    const store = new MemoryStore();
    writeCredentials(store, { apiKeyId: 'key-1', privateKeyPem: 'x' });
    clearCredentials(store);
    expect(readCredentials(store)).toBeNull();
  });

  it('returns null for malformed stored JSON rather than throwing', () => {
    const store = new MemoryStore();
    store.setItem('kalshi_api_credentials_v1', 'not json');
    expect(() => readCredentials(store)).not.toThrow();
    expect(readCredentials(store)).toBeNull();
  });

  it('returns null for a shape missing required fields', () => {
    const store = new MemoryStore();
    store.setItem('kalshi_api_credentials_v1', JSON.stringify({ apiKeyId: 'only-this' }));
    expect(readCredentials(store)).toBeNull();
  });
});
