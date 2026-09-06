/**
 * Kalshi tickers encode a fixed date: `KXHIGHNY-24JAN01-T60` = New York high
 * temperature, January 1 2024, threshold 60°F (handoff Part III, verified).
 * Format: `{SERIES}-{YY}{MON}{DD}-T{threshold}`.
 */
export interface ParsedTicker {
  readonly seriesPrefix: string;
  readonly dateMs: number; // UTC midnight of the encoded date
  readonly threshold: string;
}

const MONTH_ABBREVIATIONS: Readonly<Record<string, number>> = {
  JAN: 0,
  FEB: 1,
  MAR: 2,
  APR: 3,
  MAY: 4,
  JUN: 5,
  JUL: 6,
  AUG: 7,
  SEP: 8,
  OCT: 9,
  NOV: 10,
  DEC: 11,
};

const TICKER_PATTERN = /^([A-Z0-9]+)-(\d{2})([A-Z]{3})(\d{2})-T(.+)$/;

export function parseTicker(ticker: string): ParsedTicker | null {
  const match = TICKER_PATTERN.exec(ticker.toUpperCase());
  if (match === null) {
    return null;
  }

  const seriesPrefix = match[1];
  const yy = match[2];
  const monAbbr = match[3];
  const dd = match[4];
  const thresholdRaw = match[5];
  if (
    seriesPrefix === undefined ||
    yy === undefined ||
    monAbbr === undefined ||
    dd === undefined ||
    thresholdRaw === undefined
  ) {
    return null;
  }

  const month = MONTH_ABBREVIATIONS[monAbbr];
  if (month === undefined) {
    return null;
  }

  const year = 2000 + Number.parseInt(yy, 10);
  const day = Number.parseInt(dd, 10);
  return { seriesPrefix, dateMs: Date.UTC(year, month, day), threshold: thresholdRaw };
}
