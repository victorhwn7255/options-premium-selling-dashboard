'use client';

import { useState, useEffect } from 'react';

export interface CssColors {
  primary: string;
  secondary: string;
  accent: string;
  success: string;
  warning: string;
  error: string;
  text: string;
  textSecondary: string;
  textTertiary: string;
  textInverse: string;
  border: string;
  borderStrong: string;
  borderSubtle: string;
  surface: string;
  surfaceAlt: string;
  bgAlt: string;
  tooltipBg: string;
  tooltipText: string;
  tooltipLabel: string;
}

const DEFAULTS: CssColors = {
  primary: '#000000',
  secondary: '#000000',
  accent: '#000000',
  success: '#000000',
  warning: '#000000',
  error: '#000000',
  text: '#000000',
  textSecondary: '#525252',
  textTertiary: '#525252',
  textInverse: '#FFFFFF',
  border: '#000000',
  borderStrong: '#000000',
  borderSubtle: '#E5E5E5',
  surface: '#FFFFFF',
  surfaceAlt: '#F5F5F5',
  bgAlt: '#F5F5F5',
  tooltipBg: '#000000',
  tooltipText: '#FFFFFF',
  tooltipLabel: '#A3A3A3',
};

const VAR_MAP: Record<keyof CssColors, string> = {
  primary: '--color-primary',
  secondary: '--color-secondary',
  accent: '--color-accent',
  success: '--color-success',
  warning: '--color-warning',
  error: '--color-error',
  text: '--color-txt',
  textSecondary: '--color-txt-secondary',
  textTertiary: '--color-txt-tertiary',
  textInverse: '--color-txt-inverse',
  border: '--color-border',
  borderStrong: '--color-border-strong',
  borderSubtle: '--color-border-subtle',
  surface: '--color-surface',
  surfaceAlt: '--color-surface-alt',
  bgAlt: '--color-bg-alt',
  tooltipBg: '--color-tooltip-bg',
  tooltipText: '--color-tooltip-text',
  tooltipLabel: '--color-tooltip-label',
};

export function useCssColors(): CssColors {
  const [colors, setColors] = useState<CssColors>(DEFAULTS);

  useEffect(() => {
    function readColors() {
      const s = getComputedStyle(document.documentElement);
      const next = {} as CssColors;
      for (const [key, varName] of Object.entries(VAR_MAP)) {
        const val = s.getPropertyValue(varName).trim();
        next[key as keyof CssColors] = val || DEFAULTS[key as keyof CssColors];
      }
      setColors(next);
    }

    readColors();

    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.type === 'attributes' && m.attributeName === 'data-theme') {
          requestAnimationFrame(readColors);
        }
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  return colors;
}
