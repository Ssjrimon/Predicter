import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ARCHIVE_STORAGE_KEY, INTERACTIONS_STORAGE_KEY } from './keys';

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, '..'); // predicter-v2/src

function collectSourceFiles(dir: string): string[] {
  const files: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      files.push(...collectSourceFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry)) {
      files.push(full);
    }
  }
  return files;
}

describe('storage key literals stay frozen to keys.ts', () => {
  it('never appear as a raw string anywhere else in src/', () => {
    const offenders = collectSourceFiles(srcRoot)
      .filter((file) => !file.endsWith('keys.ts'))
      .filter((file) => {
        const content = readFileSync(file, 'utf8');
        return content.includes(ARCHIVE_STORAGE_KEY) || content.includes(INTERACTIONS_STORAGE_KEY);
      });

    expect(offenders).toEqual([]);
  });
});
