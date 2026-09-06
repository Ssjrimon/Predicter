import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev server port is deliberately NOT 5173 so this build can run side by side
// with the original Predicter app without a port collision.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5273,
    host: true,
  },
});
