import type { KeyValueStore } from './types';

/** The production `KeyValueStore`, backed by the real browser `localStorage`. */
export const localStorageAdapter: KeyValueStore = {
  getItem: (key) => window.localStorage.getItem(key),
  setItem: (key, value) => {
    window.localStorage.setItem(key, value);
  },
};
