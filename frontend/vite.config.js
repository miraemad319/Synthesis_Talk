import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/components'),
      '@utils': resolve(__dirname, './src/utils'),
      '@hooks': resolve(__dirname, './src/hooks'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: true,
    proxy: {
      // Proxy API calls to backend - FIXED: Proper configuration
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Don't rewrite the path - let the full /api/v1 path go through
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@headlessui/react', '@heroicons/react'],
          charts: ['recharts'],
          utils: ['axios', 'framer-motion'],
        },
      },
    },
  },
  optimizeDeps: {
    include: [
      'react', 
      'react-dom', 
      'axios', 
      'recharts',
      'react-dropzone',
      'react-markdown',
      'framer-motion'
    ],
  },
});