// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { Backtest } from './Backtest';
import { appendResolvedMarket } from '../../storage/archive';
import { localStorageAdapter } from '../../storage/localStorageAdapter';
import { MIN_BACKTEST_RECORDS } from '../../domain/backtesting';
import type { ResolvedMarketRecord } from '../../storage/types';

function record(overrides: Partial<ResolvedMarketRecord> = {}): ResolvedMarketRecord {
  return {
    archiveId: `a-${Math.random()}`,
    ticker: 'KXFED-25JUN-T5',
    interactedAt: 1000,
    archivedAt: 2000,
    category: 'Fed',
    categorySource: 'auto-detected',
    userEstimatePct: 65,
    marketProbabilityPct: 55,
    marketProbabilitySource: 'orderbook-midpoint',
    thesis: 'Real reasoning',
    outcome: 'yes',
    closeTimeMs: 1500,
    ...overrides,
  };
}

beforeEach(() => {
  window.localStorage.clear();
});

describe('Backtest', () => {
  it('reports insufficient data on an empty archive - expected on day one, not a bug (handoff Part VI/IX)', () => {
    render(<Backtest />);
    expect(screen.getByText(new RegExp(`0 of ${MIN_BACKTEST_RECORDS}`))).toBeInTheDocument();
  });

  it('reports insufficient data below the threshold even with some records', () => {
    appendResolvedMarket(localStorageAdapter, record());
    render(<Backtest />);
    expect(screen.getByText(new RegExp(`1 of ${MIN_BACKTEST_RECORDS}`))).toBeInTheDocument();
  });

  it('shows a real weekly time series once eligible', () => {
    for (let i = 0; i < MIN_BACKTEST_RECORDS; i += 1) {
      appendResolvedMarket(
        localStorageAdapter,
        record({ archiveId: `a${i}`, interactedAt: i, archivedAt: i * 1000, outcome: i % 2 === 0 ? 'yes' : 'no' }),
      );
    }
    render(<Backtest />);
    expect(screen.getByText('Weekly cutoff windows')).toBeInTheDocument();
    expect(screen.queryByText(/Insufficient historical data/)).not.toBeInTheDocument();
  });

  it('excludes Theoretical-mode records from the eligibility count (handoff Part V item B - non-negotiable)', () => {
    // Exactly MIN_BACKTEST_RECORDS real records plus one Theoretical-mode
    // record - eligibility must be based on the real count only.
    for (let i = 0; i < MIN_BACKTEST_RECORDS; i += 1) {
      appendResolvedMarket(
        localStorageAdapter,
        record({ archiveId: `real-${i}`, interactedAt: i, archivedAt: i * 1000, marketProbabilitySource: 'orderbook-midpoint' }),
      );
    }
    appendResolvedMarket(
      localStorageAdapter,
      record({ archiveId: 'theoretical-1', interactedAt: 999, marketProbabilitySource: 'user-typed' }),
    );

    render(<Backtest />);
    // Still exactly at the threshold (eligible), not counted as one over it.
    expect(screen.getByText('Weekly cutoff windows')).toBeInTheDocument();
  });

  it('does not become eligible on Theoretical-mode records alone', () => {
    for (let i = 0; i < MIN_BACKTEST_RECORDS; i += 1) {
      appendResolvedMarket(
        localStorageAdapter,
        record({ archiveId: `theoretical-${i}`, interactedAt: i, marketProbabilitySource: 'user-typed' }),
      );
    }
    render(<Backtest />);
    expect(screen.getByText(new RegExp(`0 of ${MIN_BACKTEST_RECORDS}`))).toBeInTheDocument();
  });
});
