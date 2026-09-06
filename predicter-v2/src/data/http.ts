/**
 * The defensive fetch pattern from the original app's `api.ts`, preserved
 * because of a real, specific failure it fixed: an empty/broken URL hit
 * Vite's SPA fallback, which returned HTML that was then parsed as JSON
 * (handoff Part IV, Phase 1). Every fetch in this layer must go through
 * this function, not a bare `fetch()` call, so that failure mode cannot
 * recur silently.
 *
 * Returns `null` (with a `console.warn`) on any failure — a non-OK
 * status, a non-JSON content type, or a thrown error — rather than
 * letting a caller accidentally treat malformed data as a real response.
 */
export async function fetchJson<T>(url: string, init?: RequestInit): Promise<T | null> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    console.warn(`[http] Request to ${url} threw before a response was received:`, error);
    return null;
  }

  if (!response.ok) {
    console.warn(`[http] Request to ${url} failed with status ${response.status}`);
    return null;
  }

  const contentType = response.headers.get('content-type');
  if (contentType === null || !contentType.includes('application/json')) {
    console.warn(`[http] Request to ${url} returned a non-JSON content-type: ${contentType}`);
    return null;
  }

  try {
    return (await response.json()) as T;
  } catch (error) {
    console.warn(`[http] Request to ${url} returned a body that failed to parse as JSON:`, error);
    return null;
  }
}
