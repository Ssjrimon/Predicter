import { useMemo, useState } from 'react';
import { MIN_BACKTEST_RECORDS, runWalkForwardBacktest } from '../../domain/backtesting';
import type { BacktestRecord } from '../../domain/backtesting';
import { readArchive } from '../../storage/archive';
import { localStorageAdapter } from '../../storage/localStorageAdapter';

function toBacktestRecord(record: ReturnType<typeof readArchive>[number]): BacktestRecord {
  return { archivedAt: record.archivedAt, predictedProbabilityPct: record.userEstimatePct, outcome: record.outcome };
}

/**
 * Showing "insufficient historical data" on a small or brand-new archive
 * is the correct behavior, not a bug (handoff Part VI) — there is no
 * partial or extrapolated chart underneath this message, because
 * `runWalkForwardBacktest` returns `timeSeries: []` before doing any
 * computation at all below the threshold (Stage 6).
 *
 * Theoretical-mode records are excluded here too, same reasoning as
 * Calibration: they compare the user's guess against their own guess of
 * the market, so including them would distort both the eligibility count
 * and the scores themselves (handoff Part V item B).
 */
export function Backtest() {
  const [refreshKey, setRefreshKey] = useState(0);
  const allRecords = useMemo(() => readArchive(localStorageAdapter), [refreshKey]);
  const records = useMemo(
    () => allRecords.filter((r) => r.marketProbabilitySource === 'orderbook-midpoint'),
    [allRecords],
  );
  const result = useMemo(() => runWalkForwardBacktest(records.map(toBacktestRecord)), [records]);

  return (
    <div className="sizer">
      <section className="card">
        <h2>Walk-Forward Backtest</h2>
        <button type="button" onClick={() => setRefreshKey((k) => k + 1)}>
          Refresh
        </button>
      </section>

      {!result.isEligible && (
        <section className="card">
          <p>
            Insufficient historical data: {result.totalRecords} of {MIN_BACKTEST_RECORDS} resolved predictions
            needed.
          </p>
        </section>
      )}

      {result.isEligible && (
        <section className="card">
          <h3>Weekly cutoff windows</h3>
          {result.timeSeries.map((window) => (
            <p key={window.cutoffMs} className="muted">
              {new Date(window.cutoffMs).toISOString().slice(0, 10)} — n={window.n}
              {window.avgBrier !== null ? `, Brier ${window.avgBrier.toFixed(4)}` : ' (insufficient data)'}
            </p>
          ))}
        </section>
      )}
    </div>
  );
}
