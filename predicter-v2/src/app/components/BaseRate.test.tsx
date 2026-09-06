// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { BaseRate } from './BaseRate';
import * as openMeteo from '../../data/openMeteo';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('BaseRate', () => {
  it('shows the disclosure that this is a real statistic, not a prediction', () => {
    render(<BaseRate />);
    expect(screen.getByText(/real Open-Meteo archive data/)).toBeInTheDocument();
    expect(screen.getByText(/not a market read, a prediction, or a guarantee/)).toBeInTheDocument();
  });

  it('reproduces the handoff-style 0% result for the verified KXHIGHNY example, as a real computation', async () => {
    vi.spyOn(openMeteo, 'fetchDailyMaxTempsForCalendarDay').mockResolvedValue([45, 50, 55, 58, 59]);
    const user = userEvent.setup();
    render(<BaseRate />);

    await user.type(screen.getByLabelText('Ticker'), 'KXHIGHNY-24JAN01-T60');
    await user.click(screen.getByRole('button', { name: 'Compute base rate' }));

    const resultSection = await screen.findByRole('region', { name: 'Base rate result' });
    expect(resultSection.textContent).toMatch(/0%/);
    expect(resultSection.textContent).toMatch(/5 years/);
  });

  it('never computes using the market\'s own year - only years strictly before it', async () => {
    const spy = vi.spyOn(openMeteo, 'fetchDailyMaxTempsForCalendarDay').mockResolvedValue([50]);
    const user = userEvent.setup();
    render(<BaseRate />);

    await user.type(screen.getByLabelText('Ticker'), 'KXHIGHNY-24JAN01-T60');
    await user.click(screen.getByRole('button', { name: 'Compute base rate' }));

    await screen.findByRole('region', { name: 'Base rate result' });
    // Ticker year is 2024; endYear passed must be 2023, not 2024.
    expect(spy).toHaveBeenCalledWith(expect.anything(), 1, 1, 2023, 10);
  });

  it('shows an error for a ticker with no parseable date/threshold, rather than silently computing garbage', async () => {
    const user = userEvent.setup();
    render(<BaseRate />);
    await user.type(screen.getByLabelText('Ticker'), 'not-a-real-ticker');
    await user.click(screen.getByRole('button', { name: 'Compute base rate' }));

    expect(await screen.findByText(/Could not parse/)).toBeInTheDocument();
  });

  it('shows null (not a fabricated 0%) when no historical data is available', async () => {
    vi.spyOn(openMeteo, 'fetchDailyMaxTempsForCalendarDay').mockResolvedValue([]);
    const user = userEvent.setup();
    render(<BaseRate />);
    await user.type(screen.getByLabelText('Ticker'), 'KXHIGHNY-24JAN01-T60');
    await user.click(screen.getByRole('button', { name: 'Compute base rate' }));

    const resultSection = await screen.findByRole('region', { name: 'Base rate result' });
    expect(resultSection.textContent).toMatch(/n\/a/);
    expect(resultSection.textContent).not.toMatch(/0%/);
  });
});
