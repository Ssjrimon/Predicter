import { useState } from 'react';
import { clearCredentials, readCredentials, writeCredentials } from '../../storage/credentials';
import { localStorageAdapter } from '../../storage/localStorageAdapter';

/**
 * Credentials are stored as plain JSON, not obfuscated — the original
 * project retired a fake XOR/base64 "encryption" scheme specifically
 * because it was not real security (handoff Part IV, Step 1). The
 * honest disclosure below is the actual security model, not a
 * placeholder for one.
 */
const SECURITY_NOTICE =
  'Your API key and private key are stored locally in this browser, in plain text. They never leave your device except to sign requests you make yourself — this app has no server-side account and no trading automation (see the live-trading gate). The security of this device is your responsibility.';

export function Settings() {
  const existing = readCredentials(localStorageAdapter);
  const [apiKeyId, setApiKeyId] = useState(existing?.apiKeyId ?? '');
  const [privateKeyPem, setPrivateKeyPem] = useState(existing?.privateKeyPem ?? '');
  const [saved, setSaved] = useState(false);

  function handleSave(): void {
    writeCredentials(localStorageAdapter, { apiKeyId: apiKeyId.trim(), privateKeyPem });
    setSaved(true);
  }

  function handleClear(): void {
    clearCredentials(localStorageAdapter);
    setApiKeyId('');
    setPrivateKeyPem('');
    setSaved(false);
  }

  return (
    <div className="sizer">
      <section className="card">
        <h2>Settings</h2>
      </section>

      <p role="alert" className="banner banner-warning">
        {SECURITY_NOTICE}
      </p>

      <section className="card">
        <label htmlFor="api-key-id">API Key ID</label>
        <input
          id="api-key-id"
          type="text"
          value={apiKeyId}
          onChange={(e) => {
            setApiKeyId(e.target.value);
            setSaved(false);
          }}
        />

        <label htmlFor="private-key-pem">Private Key (PKCS#1 PEM)</label>
        <textarea
          id="private-key-pem"
          rows={6}
          value={privateKeyPem}
          onChange={(e) => {
            setPrivateKeyPem(e.target.value);
            setSaved(false);
          }}
          placeholder="-----BEGIN RSA PRIVATE KEY-----"
        />

        <div className="row">
          <button type="button" onClick={handleSave}>
            Save
          </button>
          <button type="button" onClick={handleClear}>
            Clear
          </button>
        </div>
        {saved && <p role="status">Saved.</p>}
      </section>
    </div>
  );
}
