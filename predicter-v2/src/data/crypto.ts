/**
 * Client-side RSA-PSS SHA-256 request signing, salt length 32 (handoff
 * Part III, confirmed). The private key never leaves the browser: this
 * module only ever returns a signature string, never the key material
 * itself, to whatever calls it — the server (see `server/index.ts`) only
 * ever sees the resulting `x-kalshi-signature`/`x-kalshi-timestamp`
 * headers.
 *
 * The message-to-sign format (`timestamp + method + path`, concatenated)
 * is Kalshi's own documented signing convention. It could not be
 * independently re-verified against a live API call this session — the
 * outbound network policy blocks `external-api.kalshi.com` (see
 * PROJECT_STATUS.md's Stage 7 note) — so treat it with the same "verify
 * before trusting in production" caution as that stage's unverified wire
 * shapes, even though this specific convention is Kalshi's well-known
 * published scheme rather than a guess.
 *
 * Kalshi distributes RSA private keys in PKCS#1 form. Web Crypto's
 * `importKey('pkcs8', ...)` requires PKCS#8. That conversion is "commonly
 * skipped or done wrong" (handoff Part IV, Step 1) — getting the DER
 * length encoding wrong produces a key that fails to import (caught
 * below, returns `null`) rather than one that imports and silently signs
 * with the wrong key material.
 */

function encodeDerLength(length: number): Uint8Array<ArrayBuffer> {
  if (length < 0x80) {
    return new Uint8Array([length]);
  }
  const bytes: number[] = [];
  let remaining = length;
  while (remaining > 0) {
    bytes.unshift(remaining & 0xff);
    remaining = remaining >> 8;
  }
  return new Uint8Array([0x80 | bytes.length, ...bytes]);
}

// SEQUENCE { INTEGER 0 } for PKCS#8's algorithm-identifier version field.
const PKCS8_VERSION = new Uint8Array([0x02, 0x01, 0x00]);

// SEQUENCE { OID rsaEncryption (1.2.840.113549.1.1.1), NULL }
const RSA_ALGORITHM_IDENTIFIER = new Uint8Array([
  0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00,
]);

function pkcs1ToPkcs8(pkcs1Der: Uint8Array<ArrayBuffer>): Uint8Array<ArrayBuffer> {
  const octetString = new Uint8Array([0x04, ...encodeDerLength(pkcs1Der.length), ...pkcs1Der]);
  const body = new Uint8Array([...PKCS8_VERSION, ...RSA_ALGORITHM_IDENTIFIER, ...octetString]);
  return new Uint8Array([0x30, ...encodeDerLength(body.length), ...body]);
}

function pemToDer(pem: string): Uint8Array<ArrayBuffer> | null {
  const match = /-----BEGIN [\w ]+-----([\s\S]+?)-----END [\w ]+-----/.exec(pem);
  const base64 = match?.[1];
  if (base64 === undefined) {
    return null;
  }
  try {
    const binary = atob(base64.replace(/\s+/g, ''));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  } catch {
    return null;
  }
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

/**
 * Returns the base64-encoded RSA-PSS SHA-256 signature (salt length 32) of
 * `timestampMs + method + path`, or `null` on any failure — a malformed
 * key, a bad DER conversion, or a signing error — never a thrown
 * exception or a garbage signature (handoff Part IV, Step 1: "graceful
 * `null` return rather than silently signing garbage").
 */
export async function signKalshiRequest(
  privateKeyPkcs1Pem: string,
  timestampMs: string,
  method: string,
  path: string,
): Promise<string | null> {
  const pkcs1Der = pemToDer(privateKeyPkcs1Pem);
  if (pkcs1Der === null) {
    return null;
  }
  const pkcs8Der = pkcs1ToPkcs8(pkcs1Der);

  let cryptoKey: CryptoKey;
  try {
    cryptoKey = await crypto.subtle.importKey('pkcs8', pkcs8Der, { name: 'RSA-PSS', hash: 'SHA-256' }, false, [
      'sign',
    ]);
  } catch {
    return null;
  }

  const message = new TextEncoder().encode(`${timestampMs}${method}${path}`);
  try {
    const signature = await crypto.subtle.sign({ name: 'RSA-PSS', saltLength: 32 }, cryptoKey, message);
    return arrayBufferToBase64(signature);
  } catch {
    return null;
  }
}
