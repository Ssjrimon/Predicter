import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchJson } from './http';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

describe('fetchJson', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('returns the parsed body on a successful JSON response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ hello: 'world' })));
    const result = await fetchJson<{ hello: string }>('https://example.test/ok');
    expect(result).toEqual({ hello: 'world' });
  });

  it('returns null and warns on a non-OK status, never throwing', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ error: 'nope' }, 500)));
    const result = await fetchJson('https://example.test/broken');
    expect(result).toBeNull();
    expect(warnSpy).toHaveBeenCalledTimes(1);
  });

  it('returns null and warns when the response is HTML instead of JSON (the historical Vite SPA fallback bug)', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const htmlResponse = new Response('<!doctype html><html>...</html>', {
      status: 200,
      headers: { 'content-type': 'text/html' },
    });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(htmlResponse));
    const result = await fetchJson('https://example.test/spa-fallback');
    expect(result).toBeNull();
    expect(warnSpy).toHaveBeenCalledTimes(1);
    expect(warnSpy.mock.calls[0]?.[0]).toContain('non-JSON');
  });

  it('returns null and warns rather than throwing when fetch itself rejects', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    );
    const result = await fetchJson('https://example.test/network-error');
    expect(result).toBeNull();
    expect(warnSpy).toHaveBeenCalledTimes(1);
  });

  it('returns null and warns when the body claims JSON but fails to parse', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const brokenJsonResponse = new Response('{not valid json', {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(brokenJsonResponse));
    const result = await fetchJson('https://example.test/malformed-json');
    expect(result).toBeNull();
    expect(warnSpy).toHaveBeenCalledTimes(1);
  });
});
