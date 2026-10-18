/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        appBg: '#F4F6F9',
        surface: '#FFFFFF',
        darkBg: '#121212',
        darkSurface: '#1E1E1E',
        slateBlue: '#18416B',
        charcoal: '#343A40',
        critical: '#E53E3E',
        criticalBg: '#FDF2F2',
        lowStock: '#DD6B20',
        healthy: '#319795',
      },
    },
  },
  plugins: [],
}
