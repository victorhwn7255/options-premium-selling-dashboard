'use client';

import React from 'react';
import type { CreditPutSpreadAction } from '@/lib/types';

interface BadgeConfig {
  bgClass: string;
  borderClass: string;
  colorVar: string;
  label: string;
}

// Visual language mirrors the Naked Puts ActionChip so the dashboard reads
// consistently. SELL_CPS = success green (actionable), WATCH_CPS = accent
// purple (watchlist), WAIT/CAUTION = warning amber, AVOID = error red,
// NO_EDGE / NO_DATA = muted grey.
const ACTION_CONFIG: Record<CreditPutSpreadAction, BadgeConfig> = {
  SELL_CPS: {
    bgClass: 'bg-success-subtle',
    borderClass: 'border-success-30',
    colorVar: 'var(--color-badge-sell)',
    label: 'SELL CPS',
  },
  WATCH_CPS: {
    bgClass: 'bg-accent-subtle',
    borderClass: 'border-accent-30',
    colorVar: 'var(--color-accent)',
    label: 'WATCH',
  },
  WAIT: {
    bgClass: 'bg-warning-subtle',
    borderClass: 'border-warning-30',
    colorVar: 'var(--color-warning)',
    label: 'WAIT',
  },
  AVOID: {
    bgClass: 'bg-error-subtle',
    borderClass: 'border-error-20',
    colorVar: 'var(--color-badge-avoid)',
    label: 'AVOID',
  },
  NO_EDGE: {
    bgClass: 'bg-surface-alt',
    borderClass: 'border-border-subtle',
    colorVar: 'var(--color-txt-tertiary)',
    label: 'NO EDGE',
  },
  NO_DATA: {
    bgClass: 'bg-surface-alt',
    borderClass: 'border-border-subtle',
    colorVar: 'var(--color-txt-tertiary)',
    label: 'NO DATA',
  },
};

interface CreditPutSpreadActionBadgeProps {
  action: CreditPutSpreadAction;
  size?: 'sm' | 'md';
  title?: string;
}

export default function CreditPutSpreadActionBadge({
  action, size = 'md', title,
}: CreditPutSpreadActionBadgeProps) {
  const c = ACTION_CONFIG[action] ?? ACTION_CONFIG.NO_EDGE;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-2xs';

  return (
    <span
      title={title}
      className={[
        'inline-flex items-center rounded-full font-primary font-semibold tracking-wide',
        'border whitespace-nowrap',
        padding, c.bgClass, c.borderClass,
      ].join(' ')}
      style={{ color: c.colorVar }}
    >
      {c.label}
    </span>
  );
}
