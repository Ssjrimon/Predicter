import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

/**
 * Stage 0 placeholder.
 *
 * This exists only so the scaffold is actually runnable (`npm run dev`)
 * alongside the original build. It contains no domain logic, reads no
 * market data, and computes nothing. The real UI arrives in Stage 9.
 */
function ScaffoldPlaceholder() {
  return (
    <main style={{ font: '16px/1.5 system-ui, sans-serif', padding: '1.5rem', maxWidth: '34rem' }}>
      <h1 style={{ fontSize: '1.25rem', margin: '0 0 0.5rem' }}>Predicter v2</h1>
      <p style={{ margin: 0, opacity: 0.75 }}>
        Stage 0 scaffold. Toolchain only — no domain logic, no market data, no UI yet.
        See <code>PROJECT_STATUS.md</code> for the build stage table.
      </p>
    </main>
  );
}

const rootElement = document.getElementById('root');
if (rootElement === null) {
  throw new Error('Root element #root not found in index.html');
}

createRoot(rootElement).render(
  <StrictMode>
    <ScaffoldPlaceholder />
  </StrictMode>,
);
