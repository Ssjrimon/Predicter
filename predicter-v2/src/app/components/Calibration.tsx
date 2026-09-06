import { useMemo, useState } from 'react';
import { summarizeCalibration } from '../../domain/calibration';
import type { CalibrationSummary, ScoredRecord } from '../../domain/calibration';
import { computeHorizonBucket } from '../../domain/horizon';
import type { HorizonBucket } from '../../domain/horizon';
import { readArchive } from '../../storage/archive';
import { localStorageAdapter } from '../../storage/localStorageAdapter';
import type { ResolvedMarketRecord } from '../../storage/types';

function toUserScored(record: ResolvedMarketRecord): ScoredRecord {
  return { predictedProbability: record.userEstimatePct / 100, outcome: record.outcome === 'yes' ? 1 : 0 };
}

function toMarketScored(record: ResolvedMarketRecord): ScoredRecord {
  return { predictedProbability: record.marketProbabilityPct / 100, outcome: record.outcome === 'yes' ? 1 : 0 };
}

function formatSummary(summary: CalibrationSummary): string {
  if (summary.avgBrier === null || summary.avgLogLoss === null) {
    return `n=${summary.n} — insufficient data (min 5 required)`;
  }
  return `n=${summary.n} — Brier ${summary.avgBrier.toFixed(4)}, log loss ${summary.avgLogLoss.toFixed(4)}`;
}

/**
 * Two numbers, always shown side by side, never combined: the user's own
 * calibration and the market's, as its own separate baseline (handoff
 * Part IV, Step 4: "computes the market's log loss alongside the user's,
 * giving a baseline comparison for free"). There is no composite "skill
 * score" anywhere on this page, and there never should be (handoff Part
 * VII) — Brier and log loss are the only two numbers this view emits per
 * breakdown.
 *
 * Theoretical-mode records (`marketProbabilitySource === 'user-typed'`)
 * are excluded from every computation below — a Theoretical-mode
 * prediction compares the user's guess against their own guess of the
 * market, which would silently distort calibration (handoff Part V item
 * B; this exclusion was a non-negotiable design decision, not optional
 * polish). They still exist in the Archive, just not counted here.
 */
export function Calibration() {
  const [refreshKey, setRefreshKey] = useState(0);
  const allRecords = useMemo(() => readArchive(localStorageAdapter), [refreshKey]);
  const records = useMemo(
    () => allRecords.filter((r) => r.marketProbabilitySource === 'orderbook-midpoint'),
    [allRecords],
  );
  const excludedCount = allRecords.length - records.length;

  const overallUser = useMemo(() => summarizeCalibration(records.map(toUserScored)), [records]);
  const overallMarket = useMemo(() => summarizeCalibration(records.map(toMarketScored)), [records]);

  const byCategory = useMemo(() => {
    const groups = new Map<string, ResolvedMarketRecord[]>();
    for (const record of records) {
      const group = groups.get(record.category) ?? [];
      group.push(record);
      groups.set(record.category, group);
    }
    return [...groups.entries()].map(([category, group]) => ({
      category,
      user: summarizeCalibration(group.map(toUserScored)),
      market: summarizeCalibration(group.map(toMarketScored)),
    }));
  }, [records]);

  const byHorizon = useMemo(() => {
    const groups = new Map<HorizonBucket, ResolvedMarketRecord[]>();
    for (const record of records) {
      const bucket = computeHorizonBucket(record.closeTimeMs, record.interactedAt);
      const group = groups.get(bucket) ?? [];
      group.push(record);
      groups.set(bucket, group);
    }
    return [...groups.entries()].map(([horizon, group]) => ({
      horizon,
      user: summarizeCalibration(group.map(toUserScored)),
      market: summarizeCalibration(group.map(toMarketScored)),
    }));
  }, [records]);

  return (
    <div className="sizer">
      <section className="card">
        <h2>Calibration</h2>
        <button type="button" onClick={() => setRefreshKey((k) => k + 1)}>
          Refresh
        </button>
        {excludedCount > 0 && (
          <p className="muted">
            Excludes {excludedCount} Theoretical-mode prediction{excludedCount === 1 ? '' : 's'} (not scored — see
            Archive for the full record).
          </p>
        )}
      </section>

      <section className="card">
        <h3>Overall</h3>
        <p>You: {formatSummary(overallUser)}</p>
        <p className="muted">Market baseline: {formatSummary(overallMarket)}</p>
      </section>

      {byCategory.length > 0 && (
        <section className="card">
          <h3>By category</h3>
          {byCategory.map(({ category, user, market }) => (
            <div key={category}>
              <p>
                <strong>{category}</strong>
              </p>
              <p className="muted">You: {formatSummary(user)}</p>
              <p className="muted">Market: {formatSummary(market)}</p>
            </div>
          ))}
        </section>
      )}

      {byHorizon.length > 0 && (
        <section className="card">
          <h3>By horizon</h3>
          {byHorizon.map(({ horizon, user, market }) => (
            <div key={horizon}>
              <p>
                <strong>{horizon}</strong>
              </p>
              <p className="muted">You: {formatSummary(user)}</p>
              <p className="muted">Market: {formatSummary(market)}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
