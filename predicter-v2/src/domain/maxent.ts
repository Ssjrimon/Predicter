/**
 * Built because a research document proposed converting Fed Funds futures
 * into Kalshi probabilities via two-outcome linear interpolation — invalid
 * with 3+ live outcomes (one equation, two free parameters, underdetermined;
 * handoff Part IV). The correct approach: maximum entropy subject to the
 * known mean, the least-informative distribution consistent with what is
 * actually known.
 *
 * p_i ∝ exp(-λ · r_i), solved numerically by bisection so that
 * Σ(p_i · r_i) = targetMean. `mean(λ)` is continuous and strictly
 * decreasing (uniform at λ=0, concentrating on max(outcomes) as λ→-∞, on
 * min(outcomes) as λ→+∞), so any target strictly between min and max has
 * a unique root found by bisection after bracketing it.
 *
 * Deliberately unwired: no UI, no data source (handoff Part IV). If ever
 * surfaced, it must be labeled "Modeled distribution (maximum entropy) —
 * an estimate, not a direct market read."
 */

const MAX_BRACKET_EXPANSIONS = 40;
const MAX_BISECTION_ITERATIONS = 200;
const CONVERGENCE_TOLERANCE = 1e-10;
const BRACKET_GROWTH_FACTOR = 2;

function computeWeightsAndMean(outcomes: readonly number[], lambda: number): { weights: number[]; mean: number } {
  // Subtract the max exponent before exponentiating for numerical
  // stability, per the handoff's own description of the verified function.
  const exponents = outcomes.map((r) => -lambda * r);
  const maxExponent = Math.max(...exponents);
  const expValues = exponents.map((e) => Math.exp(e - maxExponent));
  const sumExp = expValues.reduce((a, b) => a + b, 0);
  const weights = expValues.map((e) => e / sumExp);
  const mean = outcomes.reduce((sum, r, i) => sum + r * (weights[i] ?? 0), 0);
  return { weights, mean };
}

export function solveMaxEntropyDistribution(outcomes: readonly number[], targetMean: number): number[] | null {
  if (outcomes.length < 2) {
    return null;
  }

  const min = Math.min(...outcomes);
  const max = Math.max(...outcomes);
  if (targetMean < min || targetMean > max) {
    return null;
  }

  if (targetMean === min || targetMean === max) {
    const matchCount = outcomes.filter((r) => r === targetMean).length;
    return outcomes.map((r) => (r === targetMean ? 1 / matchCount : 0));
  }

  let lambdaLow = -1;
  let lambdaHigh = 1;

  let expansions = 0;
  while (computeWeightsAndMean(outcomes, lambdaLow).mean <= targetMean) {
    lambdaLow *= BRACKET_GROWTH_FACTOR;
    expansions += 1;
    if (expansions > MAX_BRACKET_EXPANSIONS) {
      return null;
    }
  }
  expansions = 0;
  while (computeWeightsAndMean(outcomes, lambdaHigh).mean >= targetMean) {
    lambdaHigh *= BRACKET_GROWTH_FACTOR;
    expansions += 1;
    if (expansions > MAX_BRACKET_EXPANSIONS) {
      return null;
    }
  }

  for (let iteration = 0; iteration < MAX_BISECTION_ITERATIONS; iteration += 1) {
    const lambdaMid = (lambdaLow + lambdaHigh) / 2;
    const { weights, mean } = computeWeightsAndMean(outcomes, lambdaMid);
    if (Math.abs(mean - targetMean) < CONVERGENCE_TOLERANCE) {
      return weights;
    }
    if (mean > targetMean) {
      lambdaLow = lambdaMid;
    } else {
      lambdaHigh = lambdaMid;
    }
  }

  return null;
}
