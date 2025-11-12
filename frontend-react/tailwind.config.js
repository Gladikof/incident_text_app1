/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        dark: '#0f172a',
        bg: '#020617',
        'gray-light': '#94a3b8',
        danger: '#dc2626',
        success: '#16a34a',
        warning: '#f59e0b',
      },
    },
  },
  plugins: [],
}
