import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,

    // `node` by default: the domain layer is pure and must not depend on a
    // DOM to be testable. Files that genuinely need one (Web Crypto in
    // Stage 8, React components in Stage 9) opt in per-file with:
    //   // @vitest-environment jsdom
    environment: 'node',

    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
