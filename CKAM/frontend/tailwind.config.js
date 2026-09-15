/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agrigreen: {
          50: '#f2fbf5',
          100: '#e1f6e8',
          200: '#c3ecd4',
          300: '#94dcb1',
          400: '#5fc389',
          500: '#3ba76b',
          600: '#2a8553',
          700: '#236a44',
          800: '#1e5538',
          900: '#19462f',
        }
      }
    },
  },
  plugins: [],
}
