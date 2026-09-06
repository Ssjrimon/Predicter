import { useState } from 'react';
import { Sizer } from './components/Sizer';
import { Discovery } from './components/Discovery';
import { Archive } from './components/Archive';
import { Calibration } from './components/Calibration';
import { Backtest } from './components/Backtest';
import { Settings } from './components/Settings';
import { BaseRate } from './components/BaseRate';

type Tab = 'sizer' | 'discovery' | 'archive' | 'calibration' | 'backtest' | 'baserate' | 'settings';

const TABS: ReadonlyArray<{ id: Tab; label: string }> = [
  { id: 'sizer', label: 'Sizer' },
  { id: 'discovery', label: 'Discovery' },
  { id: 'archive', label: 'Archive' },
  { id: 'calibration', label: 'Calibration' },
  { id: 'backtest', label: 'Backtest' },
  { id: 'baserate', label: 'Base Rate' },
  { id: 'settings', label: 'Settings' },
];

/**
 * Tab state in App.tsx, not routes — the same convention the original
 * app used ("Navigation is tab state in App.tsx, not routes"), carried
 * forward because it's a reasonable, simple fit for a small mobile-first
 * app, not because it was ported wholesale.
 */
export function App() {
  const [activeTab, setActiveTab] = useState<Tab>('sizer');
  const [sizerTicker, setSizerTicker] = useState('');
  const [sizerKey, setSizerKey] = useState(0);

  function handleSelectTicker(ticker: string): void {
    setSizerTicker(ticker);
    setSizerKey((k) => k + 1); // force Sizer to remount with the new initial ticker
    setActiveTab('sizer');
  }

  return (
    <main>
      <header style={{ padding: '1rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.1rem', margin: 0 }}>Predicter</h1>
      </header>

      <nav className="row" style={{ justifyContent: 'center', padding: '0 1rem 1rem', flexWrap: 'wrap' }}>
        {TABS.map((tab) => (
          <button
            type="button"
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            aria-current={activeTab === tab.id}
            style={activeTab === tab.id ? { fontWeight: 'bold' } : undefined}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === 'sizer' && <Sizer key={sizerKey} initialTicker={sizerTicker} />}
      {activeTab === 'discovery' && <Discovery onSelectTicker={handleSelectTicker} />}
      {activeTab === 'archive' && <Archive />}
      {activeTab === 'calibration' && <Calibration />}
      {activeTab === 'backtest' && <Backtest />}
      {activeTab === 'baserate' && <BaseRate />}
      {activeTab === 'settings' && <Settings />}
    </main>
  );
}
