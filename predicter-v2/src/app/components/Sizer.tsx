import { useSizer } from '../hooks/useSizer';

/**
 * Mobile-first: single-column layout, no fixed widths, generous tap
 * targets. The Analysis section only renders once inputs validate
 * (handoff Part IV, Phase 1: "the Analysis card hides entirely on invalid
 * input rather than rendering nonsense") — it never shows a partial or
 * best-guess number for bad input.
 */
export function Sizer({ initialTicker }: { initialTicker?: string }) {
  const sizer = useSizer(initialTicker);

  const showAnalysis = sizer.fairProbability !== null && sizer.myEstimateValidation.valid && sizer.contractsValidation.valid;

  return (
    <div className="sizer">
      <section className="card">
        <label htmlFor="ticker">Ticker</label>
        <div className="row">
          <input
            id="ticker"
            type="text"
            value={sizer.ticker}
            onChange={(e) => sizer.setTicker(e.target.value)}
            placeholder="e.g. KXHIGHNY-24JAN01-T60"
          />
          {sizer.mode === 'live' && (
            <button type="button" onClick={() => void sizer.loadMarket()} disabled={sizer.loading}>
              {sizer.loading ? 'Loading…' : 'Load'}
            </button>
          )}
        </div>
        {sizer.loadError !== null && <p role="alert" className="error">{sizer.loadError}</p>}
      </section>

      <section className="card">
        <div className="row">
          <label>
            <input
              type="radio"
              name="mode"
              checked={sizer.mode === 'live'}
              onChange={() => sizer.setMode('live')}
            />
            Live Orderbook
          </label>
          <label>
            <input
              type="radio"
              name="mode"
              checked={sizer.mode === 'theoretical'}
              onChange={() => sizer.setMode('theoretical')}
            />
            Theoretical
          </label>
        </div>
        <div className="row">
          <label>
            <input type="radio" name="role" checked={sizer.role === 'taker'} onChange={() => sizer.setRole('taker')} />
            Taker
          </label>
          <label>
            <input type="radio" name="role" checked={sizer.role === 'maker'} onChange={() => sizer.setRole('maker')} />
            Maker (estimate)
          </label>
        </div>
      </section>

      {sizer.expiryBannerMessage !== null && (
        <p role="alert" className="banner banner-warning">
          {sizer.expiryBannerMessage}
        </p>
      )}

      {sizer.theoreticalModeWarning !== null && (
        <p role="alert" className="banner banner-warning">
          {sizer.theoreticalModeWarning}
        </p>
      )}

      {sizer.mode === 'theoretical' && (
        <section className="card">
          <label htmlFor="theoretical-price">Assumed market price (%)</label>
          <input
            id="theoretical-price"
            type="number"
            value={sizer.theoreticalPriceInput}
            onChange={(e) => sizer.setTheoreticalPriceInput(e.target.value)}
            placeholder="0-100"
          />
          {sizer.theoreticalPriceInput !== '' && !sizer.theoreticalPriceValidation.valid && (
            <p role="alert" className="error">{sizer.theoreticalPriceValidation.reason}</p>
          )}
        </section>
      )}

      <section className="card">
        <label htmlFor="my-estimate">My probability estimate (%)</label>
        <input
          id="my-estimate"
          type="number"
          value={sizer.myEstimateInput}
          onChange={(e) => sizer.setMyEstimateInput(e.target.value)}
          placeholder="0-100"
        />
        {sizer.myEstimateInput !== '' && !sizer.myEstimateValidation.valid && (
          <p role="alert" className="error">{sizer.myEstimateValidation.reason}</p>
        )}

        <label htmlFor="contracts">Contracts</label>
        <input
          id="contracts"
          type="number"
          value={sizer.contractsInput}
          onChange={(e) => sizer.setContractsInput(e.target.value)}
          placeholder="e.g. 100"
        />
        {sizer.contractsInput !== '' && !sizer.contractsValidation.valid && (
          <p role="alert" className="error">{sizer.contractsValidation.reason}</p>
        )}
      </section>

      {showAnalysis && sizer.fairProbability !== null && (
        <section className="card" aria-label="Analysis">
          <h2>Analysis</h2>
          <p>
            Fair probability: <strong>{sizer.fairProbability.pct.toFixed(1)}%</strong>{' '}
            <span className="muted">
              ({sizer.fairProbability.source === 'user-typed' ? 'your typed price' : 'orderbook midpoint'})
            </span>
          </p>

          {sizer.mode === 'live' && sizer.executableBreakeven !== null && (
            <p>
              Executable breakeven: <strong>{sizer.executableBreakeven.breakevenPct.toFixed(2)}%</strong>{' '}
              {!sizer.executableBreakeven.fullyFilled && (
                <span className="banner-warning">
                  (liquidity trap: only {sizer.executableBreakeven.filledContracts} of{' '}
                  {sizer.executableBreakeven.requestedContracts} contracts fillable — no Kelly suggestion below)
                </span>
              )}
            </p>
          )}

          {sizer.mode === 'theoretical' && sizer.theoreticalCostEstimate !== null && (
            <p>
              Theoretical cost estimate (not a real fill):{' '}
              <strong>{sizer.theoreticalCostEstimate.costBasisPct.toFixed(2)}%</strong>
            </p>
          )}

          {sizer.kellySuggestion !== null && (
            <p>
              Kelly suggestion: <strong>{(sizer.kellySuggestion * 100).toFixed(1)}%</strong> of bankroll
            </p>
          )}
        </section>
      )}

      <section className="card">
        <label htmlFor="thesis">My thesis (required to log)</label>
        <textarea
          id="thesis"
          value={sizer.thesis}
          onChange={(e) => sizer.setThesis(e.target.value)}
          rows={3}
          placeholder="Why do you believe this?"
        />
        <button type="button" onClick={sizer.logPrediction} disabled={!sizer.canLog}>
          Log Prediction
        </button>
        {sizer.logStatus === 'logged' && <p role="status">Logged.</p>}
      </section>
    </div>
  );
}
