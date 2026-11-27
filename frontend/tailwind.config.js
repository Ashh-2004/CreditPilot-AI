/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FFFFFF',
        surface: '#F4F3F3',
        border: '#E5E5E5',
        primary: {
          DEFAULT: '#191919',
          text: '#FFFFFF',
        },
        muted: 'rgba(25, 25, 25, 0.6)',
        subtle: 'rgba(25, 25, 25, 0.4)',
        risk: {
          green: '#15803d',
          amber: '#b45309',
          red: '#b91c1c',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['P22 Mackinac W01 Book', 'Georgia', 'serif'],
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        card: '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
      }
    },
  },
  plugins: [],
}
