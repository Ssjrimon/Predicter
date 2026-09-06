import { describe, expect, it } from 'vitest';
import { summarizeCalibration, MIN_CALIBRATION_SAMPLE } from './calibration';
import type { ScoredRecord } from './calibration';

function records(n: number): ScoredRecord[] {
  return Array.from({ length: n }, (_, i) => ({
    predictedProbability: 0.5,
    outcome: (i % 2) as 0 | 1,
  }));
}

describe('summarizeCalibration', () => {
  it('returns null averages below the minimum sample size, not a computed-then-hidden value', () => {
    const summary = summarizeCalibration(records(MIN_CALIBRATION_SAMPLE - 1));
    expect(summary.n).toBe(MIN_CALIBRATION_SAMPLE - 1);
    expect(summary.avgBrier).toBeNull();
    expect(summary.avgLogLoss).toBeNull();
  });

  it('computes real averages at exactly the minimum sample size', () => {
    const summary = summarizeCalibration(records(MIN_CALIBRATION_SAMPLE));
    expect(summary.n).toBe(MIN_CALIBRATION_SAMPLE);
    expect(summary.avgBrier).not.toBeNull();
    expect(summary.avgLogLoss).not.toBeNull();
    // Every record predicts 0.5 regardless of outcome -> Brier is always 0.25.
    expect(summary.avgBrier).toBeCloseTo(0.25, 10);
  });

  it('handles zero records without throwing', () => {
    const summary = summarizeCalibration([]);
    expect(summary.n).toBe(0);
    expect(summary.avgBrier).toBeNull();
    expect(summary.avgLogLoss).toBeNull();
  });

  it('never emits a composite score field - only avgBrier and avgLogLoss exist (handoff Part VII)', () => {
    const summary = summarizeCalibration(records(MIN_CALIBRATION_SAMPLE));
    expect(Object.keys(summary).sort()).toEqual(['avgBrier', 'avgLogLoss', 'n']);
  });
});
