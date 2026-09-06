import type { KeyValueStore } from './types';

/**
 * A new key for this rebuild — not one of the two frozen keys inherited
 * from the original app (there is nothing to migrate: no credentials data
 * exists to inherit, since this rebuild's archive starts empty on a
 * different origin — see PROJECT_STATUS.md). Stored as plain JSON, not
 * obfuscated: the original project retired a fake XOR/base64 "encryption"
 * scheme specifically because it wasn't real security (handoff Part IV,
 * Step 1) — real security here is the disclosure in the Settings UI, not
 * a false sense of protection from cosmetic obfuscation.
 */
const CREDENTIALS_STORAGE_KEY = 'kalshi_api_credentials_v1';

export interface KalshiCredentials {
  readonly apiKeyId: string;
  readonly privateKeyPem: string;
}

function isKalshiCredentials(value: unknown): value is KalshiCredentials {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as Record<string, unknown>)['apiKeyId'] === 'string' &&
    typeof (value as Record<string, unknown>)['privateKeyPem'] === 'string'
  );
}

export function readCredentials(store: KeyValueStore): KalshiCredentials | null {
  const raw = store.getItem(CREDENTIALS_STORAGE_KEY);
  if (raw === null) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    return isKalshiCredentials(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function writeCredentials(store: KeyValueStore, credentials: KalshiCredentials): void {
  store.setItem(CREDENTIALS_STORAGE_KEY, JSON.stringify(credentials));
}

export function clearCredentials(store: KeyValueStore): void {
  store.setItem(CREDENTIALS_STORAGE_KEY, JSON.stringify(null));
}
