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
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        databricks: {
          primary: '#FF3621',
          teal: '#1B3139',
          cream: '#F9F7F4',
        },
        agl: {
          blue: '#0066B3',
        },
        brand: {
          blue: '#3B82F6',
          green: '#10B981',
          amber: '#F59E0B',
          red: '#EF4444',
        },
      },
      accentColor: {
        'databricks-primary': '#FF3621',
      },
    },
  },
  plugins: [],
} satisfies Config;
