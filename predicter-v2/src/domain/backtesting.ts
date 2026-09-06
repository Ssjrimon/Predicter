import { summarizeCalibration } from './calibration';
import type { ScoredRecord } from './calibration';

/**
 * Deliberately a domain-local shape, not the storage layer's
 * `ResolvedMarketRecord` — the domain layer imports nothing outside
 * itself, so a caller (Stage 9/10's UI glue) maps a real archive record
 * into this minimal shape before calling into the backtest.
 */
export interface BacktestRecord {
  readonly archivedAt: number; // epoch ms
  readonly predictedProbabilityPct: number; // 0-100
  readonly outcome: 'yes' | 'no';
}

/**
 * Enforced by a real early return before any computation — no partial or
 * extrapolated output below threshold (handoff Part IV, Step 6). Showing
 * the insufficient-data message on a small or brand-new archive is
 * correct behavior, not a bug (handoff Part VI).
 */
export const MIN_BACKTEST_RECORDS = 20;

export interface CutoffWindowResult {
  readonly cutoffMs: number;
  readonly n: number;
  readonly avgBrier: number | null;
  readonly avgLogLoss: number | null;
}

export interface BacktestResult {
  readonly isEligible: boolean;
  readonly totalRecords: number;
  readonly timeSeries: readonly CutoffWindowResult[];
}

function toScoredRecord(record: BacktestRecord): ScoredRecord {
  return {
    predictedProbability: record.predictedProbabilityPct / 100,
    outcome: record.outcome === 'yes' ? 1 : 0,
  };
}

/**
 * No-lookahead guard: only records already archived at or before the
 * cutoff are visible to that cutoff's evaluation. This anchor is correct
 * because a record can only enter the archive once its outcome is already
 * known, so future information cannot leak backward into an earlier
 * cutoff point (handoff Part IV, Step 6).
 */
export function evaluateCutoffWindow(records: readonly BacktestRecord[], cutoffMs: number): CutoffWindowResult {
  const visible = records.filter((r) => r.archivedAt <= cutoffMs);
  const summary = summarizeCalibration(visible.map(toScoredRecord));
  return { cutoffMs, n: summary.n, avgBrier: summary.avgBrier, avgLogLoss: summary.avgLogLoss };
}

const WEEK_MS = 7 * 24 * 3_600_000;

/**
 * Sweeps weekly from the earliest to the latest `archivedAt`, calling the
 * same guarded {@link evaluateCutoffWindow} at every step — no bypass path
 * exists for a cutoff to skip the no-lookahead filter (handoff Part IV,
 * Step 6). Always includes the final point so the series ends at the
 * latest data, regardless of whether the span divides evenly by a week.
 */
function weeklySweep(records: readonly BacktestRecord[]): CutoffWindowResult[] {
  if (records.length === 0) {
    return [];
  }
  const timestamps = records.map((r) => r.archivedAt);
  const earliest = Math.min(...timestamps);
  const latest = Math.max(...timestamps);

  const results: CutoffWindowResult[] = [];
  for (let cutoff = earliest; cutoff < latest; cutoff += WEEK_MS) {
    results.push(evaluateCutoffWindow(records, cutoff));
  }
  results.push(evaluateCutoffWindow(records, latest));
  return results;
}

export function runWalkForwardBacktest(records: readonly BacktestRecord[]): BacktestResult {
  if (records.length < MIN_BACKTEST_RECORDS) {
    return { isEligible: false, totalRecords: records.length, timeSeries: [] };
  }
  return { isEligible: true, totalRecords: records.length, timeSeries: weeklySweep(records) };
}
