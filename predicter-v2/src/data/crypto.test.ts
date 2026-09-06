import { generateKeyPairSync } from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { signKalshiRequest } from './crypto';

function generateTestKeyPair(): { publicKeyPem: string; privateKeyPkcs1Pem: string } {
  const { publicKey, privateKey } = generateKeyPairSync('rsa', {
    modulusLength: 2048,
    publicKeyEncoding: { type: 'spki', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs1', format: 'pem' },
  });
  return { publicKeyPem: publicKey, privateKeyPkcs1Pem: privateKey };
}

async function importPublicKeyForVerify(publicKeyPem: string): Promise<CryptoKey> {
  const base64 = publicKeyPem.replace(/-----BEGIN PUBLIC KEY-----|-----END PUBLIC KEY-----|\s+/g, '');
  const binary = atob(base64);
  const der = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    der[i] = binary.charCodeAt(i);
  }
  return crypto.subtle.importKey('spki', der, { name: 'RSA-PSS', hash: 'SHA-256' }, false, ['verify']);
}

function base64ToBytes(base64: string): Uint8Array<ArrayBuffer> {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

describe('signKalshiRequest', () => {
  it('produces a signature that cryptographically verifies against the matching public key', async () => {
    const { publicKeyPem, privateKeyPkcs1Pem } = generateTestKeyPair();
    const timestamp = '1700000000000';
    const method = 'GET';
    const path = '/trade-api/v2/portfolio/balance';

    const signatureBase64 = await signKalshiRequest(privateKeyPkcs1Pem, timestamp, method, path);
    expect(signatureBase64).not.toBeNull();

    const publicKey = await importPublicKeyForVerify(publicKeyPem);
    const signatureBytes = base64ToBytes(signatureBase64 ?? '');
    const message = new TextEncoder().encode(`${timestamp}${method}${path}`);

    const isValid = await crypto.subtle.verify({ name: 'RSA-PSS', saltLength: 32 }, publicKey, signatureBytes, message);
    expect(isValid).toBe(true);
  });

  it('does NOT verify against a tampered message - proves the test above is meaningful', async () => {
    const { publicKeyPem, privateKeyPkcs1Pem } = generateTestKeyPair();
    const signatureBase64 = await signKalshiRequest(privateKeyPkcs1Pem, '1', 'GET', '/real-path');
    const publicKey = await importPublicKeyForVerify(publicKeyPem);
    const signatureBytes = base64ToBytes(signatureBase64 ?? '');
    const tamperedMessage = new TextEncoder().encode('1GET/different-path');

    const isValid = await crypto.subtle.verify(
      { name: 'RSA-PSS', saltLength: 32 },
      publicKey,
      signatureBytes,
      tamperedMessage,
    );
    expect(isValid).toBe(false);
  });

  it('returns null for a string that is not a PEM at all, rather than throwing', async () => {
    const result = await signKalshiRequest('not a real pem', '123', 'GET', '/x');
    expect(result).toBeNull();
  });

  it('returns null for a well-formed PEM wrapper around garbage DER content', async () => {
    const fakeBody = btoa('not valid der data at all');
    const fakePem = `-----BEGIN RSA PRIVATE KEY-----\n${fakeBody}\n-----END RSA PRIVATE KEY-----`;
    const result = await signKalshiRequest(fakePem, '123', 'GET', '/x');
    expect(result).toBeNull();
  });

  it('produces a different signature for a different message', async () => {
    const { privateKeyPkcs1Pem } = generateTestKeyPair();
    const sig1 = await signKalshiRequest(privateKeyPkcs1Pem, '1', 'GET', '/a');
    const sig2 = await signKalshiRequest(privateKeyPkcs1Pem, '2', 'GET', '/b');
    expect(sig1).not.toBeNull();
    expect(sig2).not.toBeNull();
    expect(sig1).not.toBe(sig2);
  });
});
