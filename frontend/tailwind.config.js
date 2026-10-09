/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Institutional University Brand & Accent
        primary: {
          DEFAULT: '#E06D3B',
          hover: '#F08252',
          deep: '#993416',
          foreground: '#FFFFFF',
        },
        nirma: {
          navy: '#0A0E1A',
          'navy-soft': '#131B2E',
          terracotta: '#E06D3B',
        },
        // Telemetry & Real-Time Voice Stream Accents
        'live-pulse': {
          DEFAULT: '#10B981',
          soft: '#34D399',
        },
        telemetry: {
          cyan: '#06B6D4',
          'cyan-soft': '#22D3EE',
          amber: '#F59E0B',
          violet: '#A855F7',
          emerald: '#10B981',
          rose: '#EF4444',
        },
        // Canvas & Surface System (Deep HPC Mission Control Dark Canvas)
        canvas: {
          DEFAULT: '#080C15',
          subtle: '#0A0E1A',
          soft: '#0D1322',
          elevated: '#131B2E',
          overlay: 'rgba(8, 12, 21, 0.85)',
        },
        // Hairline Borders & Glass Dividers
        hairline: {
          DEFAULT: 'rgba(255, 255, 255, 0.08)',
          subtle: 'rgba(255, 255, 255, 0.04)',
          strong: 'rgba(255, 255, 255, 0.16)',
          terracotta: 'rgba(224, 109, 59, 0.35)',
        },
        // Text & Content Scale
        ink: {
          DEFAULT: '#F1F5F9',
          strong: '#FFFFFF',
        },
        body: '#94A3B8',
        mute: '#64748B',
        disabled: '#475569',
        // Telecom Call State Semantic Tokens
        state: {
          queued: '#3B82F6',
          ringing: '#F59E0B',
          'in-progress': '#10B981',
          completed: '#22C55E',
          failed: '#EF4444',
          busy: '#A855F7',
          dnd: '#64748B',
        },
        border: 'rgba(255, 255, 255, 0.08)',
        input: 'rgba(255, 255, 255, 0.08)',
        ring: '#E06D3B',
        background: '#080C15',
        foreground: '#F1F5F9',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Noto Sans Gujarati', 'Noto Sans Devanagari', 'sans-serif'],
        mono: ['"SFMono-Regular"', 'Menlo', 'Monaco', 'Consolas', '"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        xs: '2px',
        sm: '4px',
        DEFAULT: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        pill: '9999px',
      },
      height: {
        control: '32px',
        'control-lg': '40px',
      },
      spacing: {
        xxs: '2px',
        xs: '4px',
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '20px',
        '2xl': '24px',
        '3xl': '32px',
        '4xl': '40px',
        '5xl': '48px',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        soundwave: 'soundwave 1.2s ease-in-out infinite alternate',
      },
      keyframes: {
        soundwave: {
          '0%': { height: '4px' },
          '100%': { height: '24px' },
        },
      },
    },
  },
  plugins: [],
};
