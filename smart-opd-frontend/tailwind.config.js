/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1E3A8A',
          hover: '#172554',
          light: '#DBEAFE',
        },
        secondary: {
          DEFAULT: '#059669',
          hover: '#047857',
        },
        surface: '#FFFFFF',
        bg: '#F9FAFB',
        text: {
          DEFAULT: '#111827',
          secondary: '#374151',
          muted: '#6B7280',
        },
        border: '#E5E7EB',
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#DC2626',
          info: '#2563EB',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}