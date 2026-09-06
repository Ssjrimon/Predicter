import express from 'express';
import type { Request, Response } from 'express';

/**
 * Proxy only. This file must never accept, store, or forward the client's
 * signing credential — the client signs requests itself (see
 * `src/data/crypto.ts`) and sends only the resulting
 * `x-kalshi-signature`/`x-kalshi-timestamp` headers, which this server
 * reads and forwards verbatim. `index.test.ts` scans this file's own
 * source text to enforce that, the same verification method the original
 * project applied to its own proxy server (handoff Part IV, Step 1).
 */

const KALSHI_BASE_URL = 'https://external-api.kalshi.com/trade-api/v2';
const PORT = process.env['PORT'] !== undefined ? Number.parseInt(process.env['PORT'], 10) : 8787;

const app = express();
app.use(express.json());

// Express 5's router (path-to-regexp v8) requires a named wildcard - a
// bare '*' throws at route-registration time, not at tsc time, since it's
// a runtime pattern string. The handler itself doesn't use the captured
// param; it rebuilds the upstream path from `req.path` directly.
app.all('/api/*splat', (req: Request, res: Response) => {
  void proxyToKalshi(req, res);
});

async function proxyToKalshi(req: Request, res: Response): Promise<void> {
  const queryIndex = req.url.indexOf('?');
  const query = queryIndex === -1 ? '' : req.url.slice(queryIndex);
  const kalshiPath = req.path.replace(/^\/api/, '');
  const targetUrl = `${KALSHI_BASE_URL}${kalshiPath}${query}`;

  const headers: Record<string, string> = { 'content-type': 'application/json' };
  const signature = req.header('x-kalshi-signature');
  const timestamp = req.header('x-kalshi-timestamp');
  if (signature !== undefined) {
    headers['x-kalshi-signature'] = signature;
  }
  if (timestamp !== undefined) {
    headers['x-kalshi-timestamp'] = timestamp;
  }

  const hasBody = req.method !== 'GET' && req.method !== 'HEAD';

  try {
    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers,
      ...(hasBody ? { body: JSON.stringify(req.body) } : {}),
    });
    const contentType = upstream.headers.get('content-type') ?? 'application/json';
    const text = await upstream.text();
    res.status(upstream.status).set('content-type', contentType).send(text);
  } catch (error) {
    console.warn(`[server] Proxy request to ${targetUrl} failed:`, error);
    res.status(502).json({ error: 'Upstream request failed' });
  }
}

app.listen(PORT, () => {
  console.log(`Predicter v2 proxy server listening on port ${PORT}`);
});
