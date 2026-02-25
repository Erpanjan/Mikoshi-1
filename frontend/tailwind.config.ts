import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './context/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        onyx: '#3B3B3D',
        platinum: '#E5E5E5',
        silver: '#A3A3A3',
        whitesmoke: '#FAFAFA',
      },
    },
  },
  plugins: [],
};

export default config;
