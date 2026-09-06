// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { Archive } from './Archive';
import { appendResolvedMarket } from '../../storage/archive';
import { localStorageAdapter } from '../../storage/localStorageAdapter';
import type { ResolvedMarketRecord } from '../../storage/types';

function record(overrides: Partial<ResolvedMarketRecord> = {}): ResolvedMarketRecord {
  return {
    archiveId: 'a1',
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

describe('Archive', () => {
  it('shows the empty state on a fresh archive - expected on day one (handoff Part IX)', () => {
    render(<Archive />);
    expect(screen.getByText('No resolved predictions yet.')).toBeInTheDocument();
  });

  it('renders a resolved record with both probability numbers and their sources', () => {
    appendResolvedMarket(localStorageAdapter, record());
    render(<Archive />);
    expect(screen.getByText('KXFED-25JUN-T5')).toBeInTheDocument();
    expect(screen.getByText(/My estimate: 65%/)).toBeInTheDocument();
    expect(screen.getByText(/Market: 55%/)).toBeInTheDocument();
  });

  it('has no edit or delete control anywhere - read-only by construction', () => {
    appendResolvedMarket(localStorageAdapter, record());
    render(<Archive />);
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /mark resolved/i })).not.toBeInTheDocument();
  });

  it('disables export buttons on an empty archive', () => {
    render(<Archive />);
    expect(screen.getByRole('button', { name: 'Export JSON' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Export CSV' })).toBeDisabled();
  });
});
