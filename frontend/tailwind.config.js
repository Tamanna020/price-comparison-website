/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          50: '#FDFBF9',
          100: '#FAF7F2', // Warm Ivory Brand Base
          200: '#F3ECE1',
          300: '#E8DDCF',
          400: '#DACABE',
          DEFAULT: '#FAF7F2',
        },
        rose: {
          50: '#FAF3F4',
          100: '#F4E5E7',
          200: '#E8CAD0',
          300: '#DCACB4',
          400: '#C98991', // Dusty Rose Brand Base
          500: '#B66F78',
          600: '#9A545D',
          700: '#7B3E45',
          DEFAULT: '#C98991',
        },
        sage: {
          50: '#F6F8F5',
          100: '#E9EFE7',
          200: '#D5DFD2',
          300: '#BED0BA',
          400: '#A8B5A0', // Soft Sage Brand Base
          500: '#8E9E86',
          600: '#72816B',
          DEFAULT: '#A8B5A0',
        },
        espresso: {
          50: '#F5F3F2',
          100: '#E6E2E0',
          200: '#C8C1BD',
          300: '#9E948F',
          400: '#6F635E',
          500: '#4D413D',
          600: '#3D332F',
          700: '#302724', // Deep Espresso Brand Base
          800: '#231B19',
          900: '#161110',
          DEFAULT: '#302724',
        },
        champagne: {
          50: '#FBF8F1',
          100: '#F5EFE0',
          200: '#EBDDC1',
          300: '#E1CAA2',
          400: '#D6BC8A', // Champagne Brand Base
          500: '#C4A569',
          600: '#A88548',
          DEFAULT: '#D6BC8A',
        },
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', '"Playfair Display"', 'Georgia', 'serif'],
        display: ['"Playfair Display"', '"Cormorant Garamond"', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft-lift': '0 10px 30px -10px rgba(48, 39, 36, 0.08)',
        'luxury-card': '0 15px 35px -12px rgba(48, 39, 36, 0.12), 0 0 1px 1px rgba(201, 137, 145, 0.12)',
        'glow-rose': '0 0 25px -5px rgba(201, 137, 145, 0.35)',
        'glow-champagne': '0 0 25px -5px rgba(214, 188, 138, 0.35)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'float-slow': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
    },
  },
  plugins: [],
}

