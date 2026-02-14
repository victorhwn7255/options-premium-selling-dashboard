/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      /* ── Colors (CSS variable-driven) ─────────── */
      colors: {
        bg:          { DEFAULT: 'var(--color-bg)', alt: 'var(--color-bg-alt)' },
        surface:     { DEFAULT: 'var(--color-surface)', alt: 'var(--color-surface-alt)', raised: 'var(--color-surface-raised)' },
        primary:     { DEFAULT: 'var(--color-primary)', hover: 'var(--color-primary-hover)', active: 'var(--color-primary-active)', subtle: 'var(--color-primary-subtle)' },
        secondary:   { DEFAULT: 'var(--color-secondary)', hover: 'var(--color-secondary-hover)', active: 'var(--color-secondary-active)', subtle: 'var(--color-secondary-subtle)' },
        accent:      { DEFAULT: 'var(--color-accent)', hover: 'var(--color-accent-hover)', active: 'var(--color-accent-active)', subtle: 'var(--color-accent-subtle)' },
        txt:         { DEFAULT: 'var(--color-txt)', secondary: 'var(--color-txt-secondary)', tertiary: 'var(--color-txt-tertiary)', inverse: 'var(--color-txt-inverse)' },
        border:      { DEFAULT: 'var(--color-border)', strong: 'var(--color-border-strong)', subtle: 'var(--color-border-subtle)' },
        success:     { DEFAULT: 'var(--color-success)', subtle: 'var(--color-success-subtle)' },
        warning:     { DEFAULT: 'var(--color-warning)', subtle: 'var(--color-warning-subtle)' },
        error:       { DEFAULT: 'var(--color-error)', subtle: 'var(--color-error-subtle)' },
        chart: {
          1: 'var(--color-chart-1)',
          2: 'var(--color-chart-2)',
          3: 'var(--color-chart-3)',
          4: 'var(--color-chart-4)',
          5: 'var(--color-chart-5)',
          6: 'var(--color-chart-6)',
        },
      },

      /* ── Typography ──────────────────────────────── */
      fontFamily: {
        primary:   ["'General Sans'", "'Sohne'", '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        secondary: ["'Source Serif 4'", "'Tiempos Text'", 'Georgia', 'serif'],
        mono:      ["'JetBrains Mono'", "'IBM Plex Mono'", "'SF Mono'", 'monospace'],
      },
      fontSize: {
        '2xs': '11px',
        'xs':  '13px',
        'sm':  '15px',
        'base':'16px',
        'lg':  '18px',
        'xl':  '21px',
        '2xl': '24px',
        '3xl': '30px',
        '4xl': '36px',
        '5xl': '48px',
        '6xl': '64px',
      },
      letterSpacing: {
        tighter: '-0.02em',
        tight:   '-0.01em',
        normal:  '0em',
        wide:    '0.01em',
        wider:   '0.04em',
        widest:  '0.08em',
      },
      lineHeight: {
        none:    '1',
        tight:   '1.2',
        snug:    '1.35',
        normal:  '1.5',
        relaxed: '1.625',
        loose:   '1.8',
      },

      /* ── Spacing ─────────────────────────────────── */
      spacing: {
        '0.5': '2px',
        '1':   '4px',
        '2':   '8px',
        '3':   '12px',
        '4':   '16px',
        '5':   '20px',
        '6':   '24px',
        '7':   '32px',
        '8':   '40px',
        '9':   '48px',
        '10':  '64px',
        '11':  '96px',
        '12':  '128px',
      },

      /* ── Radius ──────────────────────────────────── */
      borderRadius: {
        'xs':  '4px',
        'sm':  '6px',
        'md':  '8px',
        'lg':  '12px',
        'xl':  '16px',
        '2xl': '24px',
        'full':'9999px',
      },

      /* ── Shadows ───────────────────────────────── */
      boxShadow: {
        'sm':    'var(--shadow-sm)',
        'md':    'var(--shadow-md)',
        'lg':    'var(--shadow-lg)',
        'xl':    'var(--shadow-xl)',
        'focus': 'var(--shadow-focus)',
        'inner': 'inset 0 1px 2px rgba(45,40,36,0.06)',
      },

      /* ── Motion ──────────────────────────────────── */
      transitionDuration: {
        'instant': '100ms',
        'fast':    '150ms',
        'normal':  '250ms',
        'slow':    '400ms',
        'slower':  '600ms',
      },
      transitionTimingFunction: {
        'default':   'cubic-bezier(0.25, 0.1, 0.25, 1.0)',
        'ease-out':  'cubic-bezier(0.16, 1, 0.3, 1)',
        'ease-in':   'cubic-bezier(0.55, 0, 1, 0.45)',
        'ease-io':   'cubic-bezier(0.65, 0, 0.35, 1)',
        'gentle':    'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      /* ── Layout ──────────────────────────────────── */
      maxWidth: {
        'content':        '1280px',
        'content-narrow': '720px',
        'full-bleed':     '1440px',
      },

      /* ── Keyframes ───────────────────────────────── */
      keyframes: {
        'fade-in': {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.7' },
        },
        spin: {
          to: { transform: 'rotate(360deg)' },
        },
        'slide-from-right': {
          '0%':   { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-to-right': {
          '0%':   { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'fade-in':            'fade-in 400ms cubic-bezier(0.16,1,0.3,1) forwards',
        'slide-in':           'slide-in 400ms cubic-bezier(0.16,1,0.3,1) forwards',
        'pulse-glow':         'pulse-glow 2s ease-in-out infinite',
        'spin':               'spin 0.8s linear infinite',
        'slide-from-right':   'slide-from-right 200ms cubic-bezier(0.16,1,0.3,1) forwards',
        'slide-to-right':     'slide-to-right 150ms cubic-bezier(0.55,0,1,0.45) forwards',
      },
    },
  },
  plugins: [],
}
