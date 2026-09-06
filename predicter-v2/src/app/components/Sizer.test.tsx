// @vitest-environment jsdom
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Sizer } from './Sizer';
import * as kalshiClient from '../../data/kalshi/client';
import { dollars } from '../../domain/money';
import { THEORETICAL_MODE_WARNING } from '../../domain/probability';
import { ARCHIVE_STORAGE_KEY, INTERACTIONS_STORAGE_KEY } from '../../storage/keys';
import { readInteractions } from '../../storage/interactions';
import { localStorageAdapter } from '../../storage/localStorageAdapter';

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Sizer - Theoretical mode warning (handoff Part V item B)', () => {
  it('shows the exact warning text verbatim when Theoretical mode is selected', async () => {
    const user = userEvent.setup();
    render(<Sizer />);

    expect(screen.queryByText(THEORETICAL_MODE_WARNING)).not.toBeInTheDocument();

    await user.click(screen.getByLabelText('Theoretical'));

    expect(screen.getByText(THEORETICAL_MODE_WARNING)).toBeInTheDocument();
  });
});

describe('Sizer - expired-market banner (handoff Part V item A)', () => {
  it('shows the expiry banner for a market whose close_time has passed', async () => {
    vi.spyOn(kalshiClient, 'fetchMarket').mockResolvedValue({
      ticker: 'KXHIGHNY-24JAN01-T60',
      status: 'settled',
      closeTimeMs: Date.UTC(2024, 0, 1),
      result: 'yes',
      yesBidDollars: dollars(0.4),
      yesAskDollars: dollars(0.42),
    });
    vi.spyOn(kalshiClient, 'fetchOrderbook').mockResolvedValue({ yesBids: [], noBids: [] });

    const user = userEvent.setup();
    render(<Sizer />);

    await user.type(screen.getByLabelText('Ticker'), 'KXHIGHNY-24JAN01-T60');
    await user.click(screen.getByRole('button', { name: 'Load' }));

    await waitFor(() => {
      expect(screen.getByText(/closed or expired/)).toBeInTheDocument();
    });
  });
});

describe('Sizer - Analysis card visibility (handoff Part IV, Phase 1)', () => {
  it('does not render the Analysis card with no input', () => {
    render(<Sizer />);
    expect(screen.queryByRole('region', { name: 'Analysis' })).not.toBeInTheDocument();
  });

  it('does not render the Analysis card for an out-of-range probability (the 150% case)', async () => {
    const user = userEvent.setup();
    render(<Sizer />);
    await user.click(screen.getByLabelText('Theoretical'));
    await user.type(screen.getByLabelText('Assumed market price (%)'), '50');
    await user.type(screen.getByLabelText('My probability estimate (%)'), '150');
    await user.type(screen.getByLabelText('Contracts'), '100');

    expect(screen.queryByRole('region', { name: 'Analysis' })).not.toBeInTheDocument();
    expect(screen.getByText(/between 0% and 100%/)).toBeInTheDocument();
  });

  it('renders the Analysis card once all inputs are valid, in Theoretical mode', async () => {
    const user = userEvent.setup();
    render(<Sizer />);
    await user.click(screen.getByLabelText('Theoretical'));
    await user.type(screen.getByLabelText('Assumed market price (%)'), '50');
    await user.type(screen.getByLabelText('My probability estimate (%)'), '65');
    await user.type(screen.getByLabelText('Contracts'), '100');

    const analysis = screen.getByRole('region', { name: 'Analysis' });
    expect(analysis).toBeInTheDocument();
    expect(analysis.textContent).toMatch(/Fair probability/);
    expect(analysis.textContent).toMatch(/your typed price/);
  });
});

describe('Sizer - Log Prediction gating', () => {
  it('keeps the Log button disabled until a non-empty thesis is entered', async () => {
    const user = userEvent.setup();
    render(<Sizer />);
    await user.type(screen.getByLabelText('Ticker'), 'KXFED-25JUN-T5');
    await user.click(screen.getByLabelText('Theoretical'));
    await user.type(screen.getByLabelText('Assumed market price (%)'), '50');
    await user.type(screen.getByLabelText('My probability estimate (%)'), '65');
    await user.type(screen.getByLabelText('Contracts'), '100');

    const logButton = screen.getByRole('button', { name: 'Log Prediction' });
    expect(logButton).toBeDisabled();

    await user.type(screen.getByLabelText('My thesis (required to log)'), 'Real reasoning here.');
    expect(logButton).toBeEnabled();
  });

  it('also stays disabled with a thesis but no ticker - blank-ticker logging is not carried forward (handoff Part V item B)', async () => {
    const user = userEvent.setup();
    render(<Sizer />);
    await user.click(screen.getByLabelText('Theoretical'));
    await user.type(screen.getByLabelText('Assumed market price (%)'), '50');
    await user.type(screen.getByLabelText('My probability estimate (%)'), '65');
    await user.type(screen.getByLabelText('Contracts'), '100');
    await user.type(screen.getByLabelText('My thesis (required to log)'), 'Real reasoning here.');

    expect(screen.getByRole('button', { name: 'Log Prediction' })).toBeDisabled();
  });

  it('allows typing a ticker after switching to Theoretical mode first - the ticker field must never be disabled there', async () => {
    // Regression: the ticker input was previously disabled in Theoretical
    // mode while canLog still required a non-empty ticker in both modes -
    // a deadlock where a user who opened Theoretical mode directly could
    // never satisfy canLog at all. Ticker must stay editable regardless of
    // mode; only the Live-mode Load button is mode-gated.
    const user = userEvent.setup();
    render(<Sizer />);
    await user.click(screen.getByLabelText('Theoretical'));
    const tickerInput = screen.getByLabelText('Ticker');
    expect(tickerInput).toBeEnabled();

    await user.type(tickerInput, 'KXFED-25JUN-T5');
    await user.type(screen.getByLabelText('Assumed market price (%)'), '50');
    await user.type(screen.getByLabelText('My probability estimate (%)'), '65');
    await user.type(screen.getByLabelText('Contracts'), '100');
    await user.type(screen.getByLabelText('My thesis (required to log)'), 'Real reasoning here.');

    expect(screen.getByRole('button', { name: 'Log Prediction' })).toBeEnabled();
  });

  it('records a Theoretical-mode prediction with source "user-typed", excluded from live-mode contamination', async () => {
    const user = userEvent.setup();
    render(<Sizer />);
    await user.type(screen.getByLabelText('Ticker'), 'KXFED-25JUN-T5');
    await user.click(screen.getByLabelText('Theoretical'));
    await user.type(screen.getByLabelText('Assumed market price (%)'), '50');
    await user.type(screen.getByLabelText('My probability estimate (%)'), '65');
    await user.type(screen.getByLabelText('Contracts'), '100');
    await user.type(screen.getByLabelText('My thesis (required to log)'), 'Real reasoning here.');

    await user.click(screen.getByRole('button', { name: 'Log Prediction' }));

    const recorded = readInteractions(localStorageAdapter);
    expect(recorded).toHaveLength(1);
    expect(recorded[0]?.marketProbabilitySource).toBe('user-typed');
    expect(recorded[0]?.userEstimatePct).toBe(65);
    expect(recorded[0]?.marketProbabilityPct).toBe(50);
  });
});

describe('Sizer - storage keys stay consistent with Stage 5', () => {
  it('writes only to the frozen interactions key, never the archive key', async () => {
    const user = userEvent.setup();
    render(<Sizer />);
    await user.type(screen.getByLabelText('Ticker'), 'KXFED-25JUN-T5');
    await user.click(screen.getByLabelText('Theoretical'));
    await user.type(screen.getByLabelText('Assumed market price (%)'), '50');
    await user.type(screen.getByLabelText('My probability estimate (%)'), '65');
    await user.type(screen.getByLabelText('Contracts'), '100');
    await user.type(screen.getByLabelText('My thesis (required to log)'), 'Real reasoning here.');
    await user.click(screen.getByRole('button', { name: 'Log Prediction' }));

    expect(window.localStorage.getItem(INTERACTIONS_STORAGE_KEY)).not.toBeNull();
    expect(window.localStorage.getItem(ARCHIVE_STORAGE_KEY)).toBeNull();
  });
});
