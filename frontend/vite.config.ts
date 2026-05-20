import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  // Load env variables from the root of the frontend folder
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        'next/navigation': path.resolve(__dirname, './src/lib/next-navigation-shim.ts'),
        'next/link': path.resolve(__dirname, './src/lib/next-link-shim.tsx'),
      },
    },
    server: {
      port: 3000,
    },
    define: {
      // Stringify the env object values to be replaced correctly by Vite's define
      'process.env': Object.entries(env).reduce((acc, [key, val]) => {
        acc[key] = val;
        return acc;
      }, {} as Record<string, string>),
    },
  };
});
