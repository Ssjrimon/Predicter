/**
 * The two frozen localStorage key literals from the original app. Kept
 * identical for consistency, per the user's instruction — even though this
 * rebuild inherits no data from the original (different origin,
 * aistudio.google.com vs localhost, so nothing actually transfers; see
 * PROJECT_STATUS.md).
 *
 * These literals must appear ONLY in this file. Every other module imports
 * the constant. `keys.test.ts` scans the entire source tree and fails if
 * either literal string turns up anywhere else — so a future edit that
 * copy-pastes the string instead of importing it gets caught immediately,
 * not discovered later as two archives silently diverging.
 */
export const ARCHIVE_STORAGE_KEY = 'kalshi_resolved_markets_archive_v1';
export const INTERACTIONS_STORAGE_KEY = 'kalshi_tracked_interactions_v1';
