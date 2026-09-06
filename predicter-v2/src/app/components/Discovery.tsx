import { useState } from 'react';
import { fetchMarket } from '../../data/kalshi/client';
import type { ParsedMarketSummary } from '../../data/kalshi/schema';

/**
 * Handoff Part IV: a prior AI-research document proposed a weighted
 * composite "volatility score" with invented, unbacktested coefficients
 * — rejected (Part VII). What's built instead is raw, separately-sortable
 * columns of real observable metrics, with this exact required label.
 *
 * Scope note: the original app auto-discovered markets by series ticker
 * and showed a 24h range from candlestick data. This rebuild could not
 * verify the `/markets?series_ticker=...` list-response envelope or the
 * candlestick response schema against a live call this session (network
 * policy blocks the host — see PROJECT_STATUS.md's Stage 7/10 notes), so
 * rather than guess at those shapes, this view accepts a manual list of
 * tickers and shows only metrics backed by the confirmed market-summary
 * fields (spread, time to close). Auto-discovery and a real volatility
 * range can be added once those shapes are verified.
 */
const DISCOVERY_LABEL = 'Discovery Aid — Sorts by real, observable metrics. Not a validated signal. Always evaluate manually before acting.';

interface DiscoveryRow {
  readonly summary: ParsedMarketSummary;
  readonly spreadDollars: number | null;
  readonly hoursToClose: number;
}

type SortKey = 'spread' | 'timeToClose';

export function Discovery({ onSelectTicker }: { onSelectTicker: (ticker: string) => void }) {
  const [tickersInput, setTickersInput] = useState('');
  const [rows, setRows] = useState<DiscoveryRow[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>('spread');
  const [loading, setLoading] = useState(false);

  async function scan(): Promise<void> {
    const tickers = tickersInput
      .split(/[\n,]/)
      .map((t) => t.trim())
      .filter((t) => t !== '');
    if (tickers.length === 0) {
      return;
    }
    setLoading(true);
    try {
      const summaries = await Promise.all(tickers.map((t) => fetchMarket(t)));
      const now = Date.now();
      const newRows: DiscoveryRow[] = [];
      for (const summary of summaries) {
        if (summary === null) {
          continue;
        }
        const spreadDollars =
          summary.yesBidDollars !== null && summary.yesAskDollars !== null
            ? summary.yesAskDollars - summary.yesBidDollars
            : null;
        newRows.push({ summary, spreadDollars, hoursToClose: (summary.closeTimeMs - now) / 3_600_000 });
      }
      setRows(newRows);
    } finally {
      setLoading(false);
    }
  }

  const sortedRows = [...rows].sort((a, b) => {
    if (sortKey === 'spread') {
      return (a.spreadDollars ?? Number.POSITIVE_INFINITY) - (b.spreadDollars ?? Number.POSITIVE_INFINITY);
    }
    return a.hoursToClose - b.hoursToClose;
  });

  return (
    <div className="sizer">
      <p role="alert" className="banner banner-warning">
        {DISCOVERY_LABEL}
      </p>

      <section className="card">
        <label htmlFor="tickers">Tickers (comma or newline separated)</label>
        <textarea
          id="tickers"
          rows={3}
          value={tickersInput}
          onChange={(e) => setTickersInput(e.target.value)}
          placeholder="KXFED-25JUN-T5, KXHIGHNY-24JAN01-T60"
        />
        <button type="button" onClick={() => void scan()} disabled={loading}>
          {loading ? 'Scanning…' : 'Scan'}
        </button>
      </section>

      {rows.length > 0 && (
        <section className="card">
          <div className="row">
            <label>
              <input type="radio" checked={sortKey === 'spread'} onChange={() => setSortKey('spread')} />
              Sort by spread
            </label>
            <label>
              <input type="radio" checked={sortKey === 'timeToClose'} onChange={() => setSortKey('timeToClose')} />
              Sort by time to close
            </label>
          </div>

          {sortedRows.map((row) => (
            <button
              type="button"
              key={row.summary.ticker}
              className="card"
              style={{ textAlign: 'left', width: '100%' }}
              onClick={() => onSelectTicker(row.summary.ticker)}
            >
              <p>
                <strong>{row.summary.ticker}</strong>
              </p>
              <p className="muted">
                Spread: {row.spreadDollars !== null ? `${(row.spreadDollars * 100).toFixed(1)}c` : 'n/a'} · Closes in{' '}
                {row.hoursToClose.toFixed(1)}h
              </p>
            </button>
          ))}
        </section>
      )}
    </div>
  );
}
