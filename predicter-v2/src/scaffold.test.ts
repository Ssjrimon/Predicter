import { describe, expect, it } from 'vitest';

/**
 * Stage 0 sanity check only. Proves the Vitest + tsconfig + strict-mode
 * harness actually runs before any domain code is written on top of it.
 * Delete this once Stage 1 adds real tests.
 */
describe('scaffold', () => {
  it('runs under the strict tsconfig without type errors', () => {
    const values: readonly number[] = [1, 2, 3];
    // With noUncheckedIndexedAccess, this is `number | undefined` at the
    // type level even though the array is non-empty — exactly the guard
    // that will matter for orderbook levels in Stage 2.
    const first: number | undefined = values[0];
    expect(first).toBe(1);
  });
});
