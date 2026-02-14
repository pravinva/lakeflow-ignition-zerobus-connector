import type { Config } from 'tailwindcss';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const configDir = dirname(fileURLToPath(import.meta.url));

export default {
  content: [
    resolve(configDir, 'index.html'),
    resolve(configDir, 'src/**/*.{ts,tsx}'),
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          blue: '#3B82F6',
          green: '#10B981',
          amber: '#F59E0B',
          red: '#EF4444',
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
