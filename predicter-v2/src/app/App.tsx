import { Sizer } from './components/Sizer';

export function App() {
  return (
    <main>
      <header style={{ padding: '1rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.1rem', margin: 0 }}>Predicter</h1>
      </header>
      <Sizer />
    </main>
  );
}
