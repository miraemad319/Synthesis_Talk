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
      // Proxy API calls to backend - FIXED: Don't rewrite the path
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Remove the rewrite - let the full path go through
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
   proxy: {
     // Proxy ANY upload/, chat/, context/, etc. directly to port-8000
     '/upload': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     '/chat': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     '/context': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     '/insights': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     '/visualize': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     '/search': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     '/export': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     '/tools': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
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
        },
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'axios', 'recharts'],
  },
});