import { useState } from 'react';
import { fetchDailyMaxTempsForCalendarDay } from '../../data/openMeteo';
import { computeExceedanceBaseRate } from '../../domain/baseRate';
import { KNOWN_WEATHER_LOCATIONS } from '../../domain/weatherLocations';
import type { WeatherLocationName } from '../../domain/weatherLocations';
import { parseTicker } from '../../domain/ticker';

const DISCLOSURE =
  'Historical base rate from real Open-Meteo archive data for the parsed calendar day across prior years. A real statistic, not a market read, a prediction, or a guarantee about this specific occurrence.';

/**
 * Deliberately narrower than the original app: location is an explicit
 * selection, not inferred from the ticker prefix, because only
 * `KXHIGHNY`'s prefix-to-city mapping is confirmed by the handoff — Miami
 * and Austin are named as verified results but their exact ticker
 * prefixes are not given, so this does not guess at them.
 */
export function BaseRate() {
  const [ticker, setTicker] = useState('');
  const [locationName, setLocationName] = useState<WeatherLocationName>('New York, NY');
  const [yearsBack, setYearsBack] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ rate: number | null; n: number; thresholdFahrenheit: number } | null>(null);

  async function compute(): Promise<void> {
    setError(null);
    setResult(null);
    const parsed = parseTicker(ticker.trim());
    if (parsed === null) {
      setError('Could not parse a date and threshold from this ticker (expected e.g. KXHIGHNY-24JAN01-T60).');
      return;
    }
    const thresholdFahrenheit = Number.parseFloat(parsed.threshold);
    if (!Number.isFinite(thresholdFahrenheit)) {
      setError('This ticker\'s threshold is not a plain number — cannot compute an exceedance base rate.');
      return;
    }

    const date = new Date(parsed.dateMs);
    const month = date.getUTCMonth() + 1;
    const day = date.getUTCDate();
    // Years strictly before the market's own year - a base rate must
    // never be computed using the very day it's meant to inform about.
    const endYear = date.getUTCFullYear() - 1;

    setLoading(true);
    try {
      const location = KNOWN_WEATHER_LOCATIONS[locationName];
      const temps = await fetchDailyMaxTempsForCalendarDay(location, month, day, endYear, yearsBack);
      if (temps === null) {
        setError('Could not load historical weather data.');
        return;
      }
      setResult({ rate: computeExceedanceBaseRate(temps, thresholdFahrenheit), n: temps.length, thresholdFahrenheit });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="sizer">
      <p role="alert" className="banner banner-warning">
        {DISCLOSURE}
      </p>

      <section className="card">
        <label htmlFor="base-rate-ticker">Ticker</label>
        <input
          id="base-rate-ticker"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="e.g. KXHIGHNY-24JAN01-T60"
        />

        <label htmlFor="base-rate-location">City</label>
        <select
          id="base-rate-location"
          value={locationName}
          onChange={(e) => setLocationName(e.target.value as WeatherLocationName)}
        >
          {Object.keys(KNOWN_WEATHER_LOCATIONS).map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>

        <label htmlFor="base-rate-years">Years of history</label>
        <input
          id="base-rate-years"
          type="number"
          value={yearsBack}
          onChange={(e) => setYearsBack(Number.parseInt(e.target.value, 10) || 1)}
        />

        <button type="button" onClick={() => void compute()} disabled={loading}>
          {loading ? 'Computing…' : 'Compute base rate'}
        </button>
        {error !== null && <p role="alert" className="error">{error}</p>}
      </section>

      {result !== null && (
        <section className="card" aria-label="Base rate result">
          <p>
            Exceeded {result.thresholdFahrenheit}°F on this calendar day in{' '}
            <strong>
              {result.rate === null ? 'n/a' : `${(result.rate * 100).toFixed(0)}%`}
            </strong>{' '}
            of {result.n} year{result.n === 1 ? '' : 's'} of history.
          </p>
          {result.n === 0 && <p className="muted">No historical data available for this day.</p>}
        </section>
      )}
    </div>
  );
}
