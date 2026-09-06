import { useMemo, useState } from 'react';
import { exportArchiveCsv, exportArchiveJson, readArchive } from '../../storage/archive';
import { localStorageAdapter } from '../../storage/localStorageAdapter';

function downloadTextFile(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

/**
 * Read-only by construction: this view has no edit or delete UI because
 * the underlying archive module (Stage 5) exposes no such function to
 * call. There is no "mark resolved" button here or anywhere else — the
 * outcome column is sourced strictly from Kalshi via `settlementSync.ts`.
 */
export function Archive() {
  const [refreshKey, setRefreshKey] = useState(0);
  const records = useMemo(() => readArchive(localStorageAdapter), [refreshKey]);

  return (
    <div className="sizer">
      <section className="card">
        <h2>Resolved Archive</h2>
        <p className="muted">{records.length} resolved prediction{records.length === 1 ? '' : 's'}</p>
        <div className="row">
          <button type="button" onClick={() => setRefreshKey((k) => k + 1)}>
            Refresh
          </button>
          <button
            type="button"
            disabled={records.length === 0}
            onClick={() => downloadTextFile('predicter-archive.json', exportArchiveJson(localStorageAdapter), 'application/json')}
          >
            Export JSON
          </button>
          <button
            type="button"
            disabled={records.length === 0}
            onClick={() => downloadTextFile('predicter-archive.csv', exportArchiveCsv(localStorageAdapter), 'text/csv')}
          >
            Export CSV
          </button>
        </div>
      </section>

      {records.length === 0 && (
        <section className="card">
          <p className="muted">No resolved predictions yet.</p>
        </section>
      )}

      {records.map((record) => (
        <section className="card" key={record.archiveId}>
          <p>
            <strong>{record.ticker}</strong> <span className="muted">({record.category})</span>
          </p>
          <p className="muted">
            My estimate: {record.userEstimatePct}% · Market: {record.marketProbabilityPct}% (
            {record.marketProbabilitySource === 'user-typed' ? 'typed' : 'orderbook'}) · Outcome:{' '}
            <strong>{record.outcome}</strong>
          </p>
          <p className="muted">{record.thesis}</p>
        </section>
      ))}
    </div>
  );
}
