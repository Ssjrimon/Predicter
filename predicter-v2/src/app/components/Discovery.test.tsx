// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Discovery } from './Discovery';
import * as kalshiClient from '../../data/kalshi/client';
import { dollars } from '../../domain/money';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Discovery', () => {
  it('shows the required verbatim discovery-aid label (handoff Part VII)', () => {
    render(<Discovery onSelectTicker={() => {}} />);
    expect(
      screen.getByText(
        'Discovery Aid — Sorts by real, observable metrics. Not a validated signal. Always evaluate manually before acting.',
      ),
    ).toBeInTheDocument();
  });

  it('never renders a composite/weighted score column - only real, separately-sortable metrics', () => {
    render(<Discovery onSelectTicker={() => {}} />);
    expect(screen.queryByText(/volatility score/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/composite/i)).not.toBeInTheDocument();
  });

  it('scans tickers, shows spread, and calls onSelectTicker on row click', async () => {
    vi.spyOn(kalshiClient, 'fetchMarket').mockResolvedValue({
      ticker: 'KXFED-25JUN-T5',
      status: 'open',
      closeTimeMs: Date.now() + 3_600_000,
      result: undefined,
      yesBidDollars: dollars(0.48),
      yesAskDollars: dollars(0.52),
    });
    const onSelectTicker = vi.fn();
    const user = userEvent.setup();
    render(<Discovery onSelectTicker={onSelectTicker} />);

    await user.type(screen.getByLabelText('Tickers (comma or newline separated)'), 'KXFED-25JUN-T5');
    await user.click(screen.getByRole('button', { name: 'Scan' }));

    const row = await screen.findByRole('button', { name: /KXFED-25JUN-T5/ });
    expect(row.textContent).toMatch(/Spread: 4\.0c/);

    await user.click(row);
    expect(onSelectTicker).toHaveBeenCalledWith('KXFED-25JUN-T5');
  });
});
