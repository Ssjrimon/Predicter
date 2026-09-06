import { useMemo, useState } from 'react';
import { fetchMarket, fetchOrderbook } from '../../data/kalshi/client';
import type { ParsedMarketSummary } from '../../data/kalshi/schema';
import { assignCategory } from '../../domain/category';
import { checkMarketExpiry, formatExpiryBannerMessage } from '../../domain/expiry';
import type { ExpiryVerdict } from '../../domain/expiry';
import { computeFee } from '../../domain/fees';
import type { OrderRole } from '../../domain/fees';
import { dollars } from '../../domain/money';
import { normalizeOrderBook, simulateBuy } from '../../domain/orderbook';
import type { CanonicalOrderBook } from '../../domain/orderbook';
import {
  computeExecutableBreakeven,
  fairProbabilityFromBook,
  fairProbabilityFromUserInput,
  THEORETICAL_MODE_WARNING,
} from '../../domain/probability';
import type { ExecutableBreakeven, FairProbability } from '../../domain/probability';
import { kellyFraction } from '../../domain/sizing';
import { validateContracts, validatePriceDollars, validateProbabilityPct } from '../../domain/validation';
import { localStorageAdapter } from '../../storage/localStorageAdapter';
import { recordInteraction } from '../../storage/interactions';

export type SizerMode = 'live' | 'theoretical';

/**
 * A hypothetical, single-price cost estimate for Theoretical mode.
 * Deliberately NOT the same type as {@link ExecutableBreakeven} — there is
 * no real book depth behind this number, so it must never be presented or
 * handled as if it were a real, depth-tested fill.
 */
export interface TheoreticalCostEstimate {
  readonly kind: 'theoretical-estimate';
  readonly costBasisPct: number;
}

export function useSizer() {
  const [ticker, setTicker] = useState('');
  const [mode, setMode] = useState<SizerMode>('live');
  const [role, setRole] = useState<OrderRole>('taker');
  const [myEstimateInput, setMyEstimateInput] = useState('');
  const [theoreticalPriceInput, setTheoreticalPriceInput] = useState('');
  const [contractsInput, setContractsInput] = useState('');
  const [thesis, setThesis] = useState('');

  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [marketSummary, setMarketSummary] = useState<ParsedMarketSummary | null>(null);
  const [orderbook, setOrderbook] = useState<CanonicalOrderBook | null>(null);

  const [logStatus, setLogStatus] = useState<'idle' | 'logged' | 'duplicate'>('idle');

  async function loadMarket(): Promise<void> {
    const trimmed = ticker.trim();
    if (trimmed === '') {
      setLoadError('Enter a ticker first.');
      return;
    }
    setLoading(true);
    setLoadError(null);
    setLogStatus('idle');
    try {
      const [summary, rawBook] = await Promise.all([fetchMarket(trimmed), fetchOrderbook(trimmed)]);
      if (summary === null || rawBook === null) {
        setLoadError('Could not load this market. Check the ticker and try again.');
        setMarketSummary(null);
        setOrderbook(null);
        return;
      }
      setMarketSummary(summary);
      setOrderbook(normalizeOrderBook(rawBook));
    } finally {
      setLoading(false);
    }
  }

  const myEstimatePct = Number.parseFloat(myEstimateInput);
  const myEstimateValidation = validateProbabilityPct(myEstimatePct);

  const contracts = Number.parseInt(contractsInput, 10);
  const contractsValidation = validateContracts(contracts);

  const theoreticalPricePct = Number.parseFloat(theoreticalPriceInput);
  const theoreticalPriceValidation = validateProbabilityPct(theoreticalPricePct);

  const expiryVerdict: ExpiryVerdict | null = useMemo(() => {
    if (mode !== 'live' || marketSummary === null) {
      return null;
    }
    return checkMarketExpiry({ status: marketSummary.status, closeTimeMs: marketSummary.closeTimeMs, nowMs: Date.now() });
  }, [mode, marketSummary]);

  const fairProbability: FairProbability | null = useMemo(() => {
    if (mode === 'theoretical') {
      return theoreticalPriceValidation.valid ? fairProbabilityFromUserInput(theoreticalPricePct) : null;
    }
    const bestBid = orderbook?.yesBids[0];
    const bestAsk = orderbook?.yesAsks[0];
    if (bestBid === undefined || bestAsk === undefined) {
      return null;
    }
    return fairProbabilityFromBook(bestBid.priceCents, bestAsk.priceCents);
  }, [mode, theoreticalPriceValidation.valid, theoreticalPricePct, orderbook]);

  const executableBreakeven: ExecutableBreakeven | null = useMemo(() => {
    if (mode !== 'live' || orderbook === null || !contractsValidation.valid) {
      return null;
    }
    const sim = simulateBuy({ book: orderbook, side: 'yes', contracts, role });
    return computeExecutableBreakeven(sim);
  }, [mode, orderbook, contractsValidation.valid, contracts, role]);

  const theoreticalCostEstimate: TheoreticalCostEstimate | null = useMemo(() => {
    if (mode !== 'theoretical' || !theoreticalPriceValidation.valid || !contractsValidation.valid) {
      return null;
    }
    const priceDollars = dollars(theoreticalPricePct / 100);
    if (!validatePriceDollars(priceDollars).valid) {
      return null;
    }
    const fee = computeFee({ contracts, priceDollars, role });
    const costBasisPct = theoreticalPricePct + (fee / contracts) * 100;
    return { kind: 'theoretical-estimate', costBasisPct };
  }, [mode, theoreticalPriceValidation.valid, theoreticalPricePct, contractsValidation.valid, contracts, role]);

  const costBasisPctForKelly: number | null =
    mode === 'live'
      ? executableBreakeven?.fullyFilled === true
        ? executableBreakeven.breakevenPct
        : null
      : (theoreticalCostEstimate?.costBasisPct ?? null);

  const kellySuggestion: number | null = useMemo(() => {
    if (costBasisPctForKelly === null || !myEstimateValidation.valid) {
      return null;
    }
    return kellyFraction({
      trueProbability: myEstimatePct / 100,
      costBasisDollars: dollars(costBasisPctForKelly / 100),
    });
  }, [costBasisPctForKelly, myEstimateValidation.valid, myEstimatePct]);

  const isMarketOpenForLogging = mode === 'theoretical' || expiryVerdict?.kind === 'open';

  const canLog =
    thesis.trim() !== '' &&
    myEstimateValidation.valid &&
    contractsValidation.valid &&
    fairProbability !== null &&
    isMarketOpenForLogging &&
    ticker.trim() !== '';

  function logPrediction(): void {
    if (!canLog || fairProbability === null) {
      return;
    }
    const trimmedTicker = ticker.trim();
    const closeTimeMs = mode === 'live' ? (marketSummary?.closeTimeMs ?? Date.now()) : Date.now();
    const category = assignCategory(trimmedTicker);
    recordInteraction(localStorageAdapter, {
      ticker: trimmedTicker,
      interactedAt: Date.now(),
      userEstimatePct: myEstimatePct,
      marketProbabilityPct: fairProbability.pct,
      marketProbabilitySource: fairProbability.source,
      thesis: thesis.trim(),
      closeTimeMs,
      ...(category.source === 'user-override' ? { categoryOverride: category.category } : {}),
    });
    setLogStatus('logged');
  }

  return {
    ticker,
    setTicker,
    mode,
    setMode,
    role,
    setRole,
    myEstimateInput,
    setMyEstimateInput,
    theoreticalPriceInput,
    setTheoreticalPriceInput,
    contractsInput,
    setContractsInput,
    thesis,
    setThesis,
    loading,
    loadError,
    marketSummary,
    orderbook,
    loadMarket,
    myEstimateValidation,
    contractsValidation,
    theoreticalPriceValidation,
    expiryVerdict,
    expiryBannerMessage: expiryVerdict?.kind === 'expired' ? formatExpiryBannerMessage(expiryVerdict.closeTimeMs) : null,
    theoreticalModeWarning: mode === 'theoretical' ? THEORETICAL_MODE_WARNING : null,
    fairProbability,
    executableBreakeven,
    theoreticalCostEstimate,
    kellySuggestion,
    canLog,
    logStatus,
    logPrediction,
  };
}
