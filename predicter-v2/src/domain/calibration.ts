import { brierScore, logLoss } from './scoring';
import type { BinaryOutcome } from './scoring';

/**
 * Below this, `avgBrier`/`avgLogLoss` are `null` — a real structural
 * guard, not a hidden label. The gate runs BEFORE any aggregation, so a
 * 2-record sample cannot produce a real-looking average through any path,
 * including exports (handoff Part IV, Step 4).
 */
export const MIN_CALIBRATION_SAMPLE = 5;

export interface ScoredRecord {
  readonly predictedProbability: number; // 0-1
  readonly outcome: BinaryOutcome;
}

export interface CalibrationSummary {
  readonly n: number;
  readonly avgBrier: number | null;
  readonly avgLogLoss: number | null;
}

/**
 * No blended composite "skill score" here or anywhere downstream —
 * deliberate (handoff Part VII). Brier and log loss stay two separate
 * numbers so the caller draws their own conclusions; nothing in this
 * module combines them into one.
 */
export function summarizeCalibration(records: readonly ScoredRecord[]): CalibrationSummary {
  const n = records.length;
  if (n < MIN_CALIBRATION_SAMPLE) {
    return { n, avgBrier: null, avgLogLoss: null };
  }

  let totalBrier = 0;
  let totalLogLoss = 0;
  for (const record of records) {
    totalBrier += brierScore(record.predictedProbability, record.outcome);
    totalLogLoss += logLoss(record.predictedProbability, record.outcome);
  }

  return { n, avgBrier: totalBrier / n, avgLogLoss: totalLogLoss / n };
}
