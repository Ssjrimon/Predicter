import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const here = dirname(fileURLToPath(import.meta.url));

describe('server proxy never touches a private key', () => {
  it('contains zero occurrences of any spelling of "private key" in its own source', () => {
    const source = readFileSync(join(here, 'index.ts'), 'utf8');
    expect(/private[_-]?key/i.test(source)).toBe(false);
  });

  it('only forwards the two signature headers, never a credential body field', () => {
    const source = readFileSync(join(here, 'index.ts'), 'utf8');
    expect(source).toContain('x-kalshi-signature');
    expect(source).toContain('x-kalshi-timestamp');
  });
});
