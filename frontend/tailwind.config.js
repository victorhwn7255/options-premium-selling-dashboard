/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      /* ── Colors (CSS variable-driven, monochrome) ─── */
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
        /* New design system names */
        display: ["'Playfair Display'", 'Georgia', 'serif'],
        body:    ["'Source Serif 4'", 'Georgia', 'serif'],
        mono:    ["'JetBrains Mono'", 'monospace'],
        /* Aliases for existing component classes */
        primary:   ["'Playfair Display'", 'Georgia', 'serif'],
        secondary: ["'Source Serif 4'", 'Georgia', 'serif'],
      },
      fontSize: {
        '2xs': ['11px', { lineHeight: '1.5' }],
        'xs':  ['12px', { lineHeight: '1.5' }],
        'sm':  ['14px', { lineHeight: '1.5' }],
        'base':['16px', { lineHeight: '1.625' }],
        'lg':  ['18px', { lineHeight: '1.625' }],
        'xl':  ['20px', { lineHeight: '1.5' }],
        '2xl': ['24px', { lineHeight: '1.35' }],
        '3xl': ['32px', { lineHeight: '1.2' }],
        '4xl': ['40px', { lineHeight: '1.1' }],
        '5xl': ['56px', { lineHeight: '1.1' }],
        '6xl': ['72px', { lineHeight: '1.0' }],
        '7xl': ['96px', { lineHeight: '1.0' }],
        '8xl': ['128px', { lineHeight: '1.0' }],
        '9xl': ['160px', { lineHeight: '1.0' }],
      },
      letterSpacing: {
        tighter: '-0.05em',
        tight:   '-0.025em',
        normal:  '0em',
        wide:    '0.025em',
        wider:   '0.05em',
        widest:  '0.1em',
      },
      lineHeight: {
        none:    '1',
        tight:   '1.1',
        snug:    '1.2',
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

      /* ── Border Radius — ALL 0px ─────────────────── */
      borderRadius: {
        'none': '0px',
        DEFAULT: '0px',
        'xs':  '0px',
        'sm':  '0px',
        'md':  '0px',
        'lg':  '0px',
        'xl':  '0px',
        '2xl': '0px',
        'full': '0px',
      },

      /* ── Shadows — ALL none ──────────────────────── */
      boxShadow: {
        'none':    'none',
        DEFAULT:   'none',
        'sm':      'none',
        'md':      'none',
        'lg':      'none',
        'xl':      'none',
        '2xl':     'none',
        'focus':   'none',
        'inner':   'none',
      },

      /* ── Border Width ────────────────────────────── */
      borderWidth: {
        DEFAULT:  '1px',
        '0':      '0px',
        '2':      '2px',
        '4':      '4px',
        '8':      '8px',
        hairline: '1px',
        thin:     '1px',
        medium:   '2px',
        thick:    '4px',
        ultra:    '8px',
      },

      /* ── Motion — minimal ────────────────────────── */
      transitionDuration: {
        'instant': '0ms',
        'snap':    '100ms',
        'fast':    '100ms',
        'normal':  '100ms',
        'slow':    '100ms',
        'slower':  '100ms',
      },
      transitionTimingFunction: {
        'default':   'linear',
        'ease-out':  'linear',
        'ease-in':   'linear',
        'ease-io':   'linear',
        'gentle':    'linear',
      },

      /* ── Layout ──────────────────────────────────── */
      maxWidth: {
        'content':        '1152px',
        'content-narrow': '720px',
        'full-bleed':     '1440px',
      },

      /* ── Keyframes ───────────────────────────────── */
      keyframes: {
        'fade-in': {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-in': {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        spin: {
          to: { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'fade-in':    'fade-in 100ms linear forwards',
        'slide-in':   'slide-in 100ms linear forwards',
        'spin':       'spin 0.8s linear infinite',
        'ping':       'ping 1s linear infinite',
      },
    },
  },
  plugins: [],
}
