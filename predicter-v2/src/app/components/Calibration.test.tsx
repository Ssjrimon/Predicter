// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { Calibration } from './Calibration';
import { appendResolvedMarket } from '../../storage/archive';
import { localStorageAdapter } from '../../storage/localStorageAdapter';
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

describe('Calibration', () => {
  it('shows insufficient-data for both You and Market below the sample gate (n<5)', () => {
    appendResolvedMarket(localStorageAdapter, record());
    render(<Calibration />);
    const overall = screen.getByText('Overall').closest('section');
    expect(overall?.textContent).toMatch(/insufficient data/);
    expect(overall?.textContent).toContain('You:');
    expect(overall?.textContent).toContain('Market baseline:');
  });

  it('shows two separate real numbers - never one blended score - at n>=5', () => {
    for (let i = 0; i < 5; i += 1) {
      appendResolvedMarket(
        localStorageAdapter,
        record({ archiveId: `a${i}`, interactedAt: i, outcome: i % 2 === 0 ? 'yes' : 'no' }),
      );
    }
    render(<Calibration />);
    const overall = screen.getByText('Overall').closest('section');
    expect(overall?.textContent).toMatch(/Brier \d/);
    expect(overall?.textContent).toMatch(/log loss \d/);
    // Never a single combined "skill score" field (handoff Part VII).
    expect(screen.queryByText(/skill score/i)).not.toBeInTheDocument();
  });

  it('groups by category', () => {
    for (let i = 0; i < 5; i += 1) {
      appendResolvedMarket(
        localStorageAdapter,
        record({ archiveId: `a${i}`, interactedAt: i, category: 'Weather', outcome: 'yes' }),
      );
    }
    render(<Calibration />);
    expect(screen.getByText('By category')).toBeInTheDocument();
    expect(screen.getByText('Weather')).toBeInTheDocument();
  });
});
