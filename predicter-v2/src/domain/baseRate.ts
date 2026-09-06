/**
 * A Kalshi high-temperature market ("will the high be greater than X°F")
 * resolves YES when the actual high strictly exceeds the threshold — the
 * handoff's own worked examples ("Miami 0% for 95°F", "NYC 0% ... for
 * exceeding 60°F") use exceedance framing, so this uses strict `>`, not
 * `>=`.
 *
 * `null` only when there is no historical data at all — never a
 * fabricated 0% presented as if it were a real answer to "never happens"
 * versus "no data available," which are different claims.
 */
export function computeExceedanceBaseRate(dailyMaxTemps: readonly number[], thresholdFahrenheit: number): number | null {
  if (dailyMaxTemps.length === 0) {
    return null;
  }
  const exceedCount = dailyMaxTemps.filter((t) => t > thresholdFahrenheit).length;
  return exceedCount / dailyMaxTemps.length;
}
