import { fetchJson } from './http';
import type { WeatherLocation } from '../domain/weatherLocations';

/**
 * UNVERIFIED WIRE SHAPE. Open-Meteo's archive API
 * (`https://archive-api.open-meteo.com/v1/archive`) is a real, documented
 * public API, but this session's outbound network policy blocks it too
 * (confirmed via the agent proxy: "connect_rejected ... organization
 * policy" — the same general block that affects `external-api.kalshi.com`,
 * not something specific to Kalshi). This interface reflects Open-Meteo's
 * publicly documented response shape from general knowledge, not a live
 * response inspected this session. Verify against a real call before
 * trusting it, same discipline as `data/kalshi/schema.ts`.
 */
export interface RawArchiveResponse {
  readonly daily: {
    readonly time: readonly string[]; // 'YYYY-MM-DD'
    readonly temperature_2m_max: readonly (number | null)[];
  };
}

/**
 * Fetches one multi-year range in a single request and filters
 * client-side for the matching calendar day across years — the "10-year
 * archive" approach the handoff describes (Part IV), rather than one
 * request per year.
 *
 * `endYear` should be the year strictly BEFORE the market's own year, so
 * a base rate is never computed using the very day it's meant to predict
 * (a no-lookahead discipline, same principle as Stage 6's backtest guard,
 * applied here to a data range rather than an archive cutoff).
 */
export async function fetchDailyMaxTempsForCalendarDay(
  location: WeatherLocation,
  month: number,
  day: number,
  endYear: number,
  yearsBack: number,
): Promise<number[] | null> {
  const startYear = endYear - yearsBack + 1;
  const startDate = `${startYear}-01-01`;
  const endDate = `${endYear}-12-31`;
  const url =
    `https://archive-api.open-meteo.com/v1/archive?latitude=${location.latitude}&longitude=${location.longitude}` +
    `&start_date=${startDate}&end_date=${endDate}&daily=temperature_2m_max&temperature_unit=fahrenheit` +
    `&timezone=${encodeURIComponent(location.timezone)}`;

  const data = await fetchJson<RawArchiveResponse>(url);
  if (data === null) {
    return null;
  }

  const results: number[] = [];
  const { time, temperature_2m_max: temps } = data.daily;
  for (let i = 0; i < time.length; i += 1) {
    const dateStr = time[i];
    const temp = temps[i];
    if (dateStr === undefined || temp === null || temp === undefined) {
      continue;
    }
    const parts = dateStr.split('-');
    const mm = parts[1];
    const dd = parts[2];
    if (mm === undefined || dd === undefined) {
      continue;
    }
    if (Number.parseInt(mm, 10) === month && Number.parseInt(dd, 10) === day) {
      results.push(temp);
    }
  }
  return results;
}
