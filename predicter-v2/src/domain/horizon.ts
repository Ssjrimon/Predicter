export type HorizonBucket = '<24h' | '1-7d' | '7-30d' | '30+d';

const MS_PER_HOUR = 3_600_000;
const MS_PER_DAY = 24 * MS_PER_HOUR;

/** Bucketed from `closeTimeMs - loggedAtMs` (handoff Part IV, Step 4). */
export function computeHorizonBucket(closeTimeMs: number, loggedAtMs: number): HorizonBucket {
  const deltaMs = closeTimeMs - loggedAtMs;
  if (deltaMs < MS_PER_DAY) {
    return '<24h';
  }
  if (deltaMs < 7 * MS_PER_DAY) {
    return '1-7d';
  }
  if (deltaMs < 30 * MS_PER_DAY) {
    return '7-30d';
  }
  return '30+d';
}
