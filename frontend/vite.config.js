// vite.config.js (replace entire file with this)
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // no root or publicDir overrides
});
