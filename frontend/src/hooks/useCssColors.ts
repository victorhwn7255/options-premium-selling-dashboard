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
  primary: '#C47B5A',
  secondary: '#7D8C6E',
  accent: '#8B8FC7',
  success: '#6B8C5A',
  warning: '#C49A5A',
  error: '#C45A5A',
  text: '#2D2824',
  textSecondary: '#6B5F54',
  textTertiary: '#9A8E82',
  textInverse: '#FAF7F4',
  border: '#E8E0D5',
  borderStrong: '#D1C7B8',
  borderSubtle: '#F0EAE2',
  surface: '#FFFFFF',
  surfaceAlt: '#F0EAE2',
  bgAlt: '#F5F0EB',
  tooltipBg: '#2D2824',
  tooltipText: '#FAF7F4',
  tooltipLabel: '#B8ADA2',
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
