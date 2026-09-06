// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { Settings } from './Settings';
import { readCredentials } from '../../storage/credentials';
import { localStorageAdapter } from '../../storage/localStorageAdapter';

beforeEach(() => {
  window.localStorage.clear();
});

describe('Settings', () => {
  it('shows the security disclosure about plain-text local storage', () => {
    render(<Settings />);
    expect(screen.getByText(/stored locally in this browser, in plain text/)).toBeInTheDocument();
    expect(screen.getByText(/no trading automation/)).toBeInTheDocument();
  });

  it('saves and reads back credentials via the storage layer, not ad hoc state', async () => {
    const user = userEvent.setup();
    render(<Settings />);
    await user.type(screen.getByLabelText('API Key ID'), 'my-key-id');
    await user.type(screen.getByLabelText('Private Key (PKCS#1 PEM)'), '-----BEGIN RSA PRIVATE KEY-----');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(readCredentials(localStorageAdapter)).toEqual({
      apiKeyId: 'my-key-id',
      privateKeyPem: '-----BEGIN RSA PRIVATE KEY-----',
    });
  });

  it('clears stored credentials', async () => {
    const user = userEvent.setup();
    render(<Settings />);
    await user.type(screen.getByLabelText('API Key ID'), 'my-key-id');
    await user.click(screen.getByRole('button', { name: 'Save' }));
    await user.click(screen.getByRole('button', { name: 'Clear' }));

    expect(readCredentials(localStorageAdapter)).toBeNull();
  });
});
