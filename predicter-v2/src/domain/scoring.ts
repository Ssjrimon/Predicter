/**
 * Without a clamp, a single prediction logged at exactly 0% or 100% that
 * resolves the other way produces `-ln(0) = Infinity` and silently
 * destroys any average it's folded into (handoff Part IV, Step 4).
 */
export const LOG_LOSS_EPSILON = 0.001;

export type BinaryOutcome = 0 | 1;

/** Brier score: (p - y)^2. Lower is better; range [0, 1]. */
export function brierScore(predictedProbability: number, outcome: BinaryOutcome): number {
  return (predictedProbability - outcome) ** 2;
}

/**
 * Log loss: -[y*ln(p) + (1-y)*ln(1-p)], with `p` clamped to
 * [LOG_LOSS_EPSILON, 1 - LOG_LOSS_EPSILON] so a boundary prediction never
 * produces `Infinity`.
 */
export function logLoss(predictedProbability: number, outcome: BinaryOutcome): number {
  const clamped = Math.min(1 - LOG_LOSS_EPSILON, Math.max(LOG_LOSS_EPSILON, predictedProbability));
  return -(outcome * Math.log(clamped) + (1 - outcome) * Math.log(1 - clamped));
}
