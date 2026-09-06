import { describe, expect, it } from 'vitest';
import { evaluateCutoffWindow, MIN_BACKTEST_RECORDS, runWalkForwardBacktest } from './backtesting';
import type { BacktestRecord } from './backtesting';

function makeRecords(n: number, archivedAtOf: (i: number) => number = () => 0): BacktestRecord[] {
  return Array.from({ length: n }, (_, i) => ({
    archivedAt: archivedAtOf(i),
    predictedProbabilityPct: 50 + (i % 2 === 0 ? 10 : -10),
    outcome: i % 2 === 0 ? 'yes' : 'no',
  }));
}

describe('MIN_BACKTEST_RECORDS', () => {
  it('is 20, per the handoff', () => {
    expect(MIN_BACKTEST_RECORDS).toBe(20);
  });
});

describe('runWalkForwardBacktest', () => {
  it('returns ineligible with an empty time series below the threshold - no partial output', () => {
    const result = runWalkForwardBacktest(makeRecords(MIN_BACKTEST_RECORDS - 1));
    expect(result.isEligible).toBe(false);
    expect(result.totalRecords).toBe(MIN_BACKTEST_RECORDS - 1);
    expect(result.timeSeries).toEqual([]);
  });

  it('correctly reports insufficient data on a brand-new (empty) archive - expected, not a bug (handoff Part VI)', () => {
    const result = runWalkForwardBacktest([]);
    expect(result.isEligible).toBe(false);
    expect(result.totalRecords).toBe(0);
    expect(result.timeSeries).toEqual([]);
  });

  it('becomes eligible at exactly the threshold', () => {
    const result = runWalkForwardBacktest(makeRecords(MIN_BACKTEST_RECORDS));
    expect(result.isEligible).toBe(true);
    expect(result.totalRecords).toBe(MIN_BACKTEST_RECORDS);
    expect(result.timeSeries.length).toBeGreaterThan(0);
  });

  it('the weekly sweep always ends exactly at the latest archivedAt', () => {
    const WEEK = 7 * 24 * 3_600_000;
    const records = makeRecords(MIN_BACKTEST_RECORDS, (i) => i * WEEK); // spans ~20 weeks
    const result = runWalkForwardBacktest(records);
    const last = result.timeSeries.at(-1);
    expect(last?.cutoffMs).toBe((MIN_BACKTEST_RECORDS - 1) * WEEK);
  });
});

describe('evaluateCutoffWindow — no-lookahead guard', () => {
  it('excludes records archived after the cutoff (handoff Part IV, Step 6)', () => {
    const records: BacktestRecord[] = [
      { archivedAt: 0, predictedProbabilityPct: 60, outcome: 'yes' },
      { archivedAt: 100, predictedProbabilityPct: 40, outcome: 'no' },
      { archivedAt: 200, predictedProbabilityPct: 70, outcome: 'yes' },
    ];

    expect(evaluateCutoffWindow(records, 50).n).toBe(1);
    expect(evaluateCutoffWindow(records, 150).n).toBe(2);
    expect(evaluateCutoffWindow(records, 200).n).toBe(3);
    expect(evaluateCutoffWindow(records, -1).n).toBe(0);
  });

  it('includes a record archived exactly at the cutoff (<=, not <)', () => {
    const records: BacktestRecord[] = [{ archivedAt: 100, predictedProbabilityPct: 50, outcome: 'yes' }];
    expect(evaluateCutoffWindow(records, 100).n).toBe(1);
    expect(evaluateCutoffWindow(records, 99).n).toBe(0);
  });

  it('still applies the calibration sample gate within each cutoff window', () => {
    const records = makeRecords(4, () => 0); // below MIN_CALIBRATION_SAMPLE (5)
    const result = evaluateCutoffWindow(records, 0);
    expect(result.n).toBe(4);
    expect(result.avgBrier).toBeNull();
    expect(result.avgLogLoss).toBeNull();
  });
});
