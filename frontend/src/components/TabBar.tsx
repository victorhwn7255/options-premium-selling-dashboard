'use client';

import React from 'react';

export type DashboardTab = 'naked-puts' | 'credit-put-spreads' | 'journal' | 'shadow';

interface TabDefinition {
  id: DashboardTab;
  label: string;
  suffix?: string;
  // When set, the tab can still be clicked but renders dimmed + tooltip.
  comingSoon?: boolean;
}

const TABS: TabDefinition[] = [
  { id: 'naked-puts',           label: 'Naked Puts' },
  { id: 'credit-put-spreads',   label: 'Credit Put Spreads' },
  { id: 'journal',              label: 'Journal' },
];

// Operator-only tab (Phase B, transitional — removed at Phase E). Appended when the
// viewer is the authenticated owner (same identity as the journal).
const SHADOW_TAB: TabDefinition = { id: 'shadow', label: 'Shadow', suffix: 'v2' };

interface TabBarProps {
  activeTab: DashboardTab;
  onChange: (tab: DashboardTab) => void;
  showShadow?: boolean;
}

/**
 * Dashboard-level tab switcher. Sits BELOW the Market Regime Banner so the
 * regime context stays visible across all tabs (per Phase 4 layout spec).
 */
export default function TabBar({ activeTab, onChange, showShadow = false }: TabBarProps) {
  const tabs = showShadow ? [...TABS, SHADOW_TAB] : TABS;
  return (
    <div
      role="tablist"
      aria-label="Strategy view"
      className="flex items-end gap-1 border-b border-border-subtle mb-5 -mx-1 px-1"
    >
      {tabs.map(tab => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            id={`tab-${tab.id}`}
            onClick={() => onChange(tab.id)}
            title={tab.comingSoon ? `${tab.label} — ${tab.suffix}` : undefined}
            className={[
              'relative px-3.5 sm:px-4 py-2 text-xs sm:text-sm font-medium font-primary',
              'rounded-t-md transition-colors duration-fast outline-none',
              'focus-visible:ring-2 focus-visible:ring-primary-30',
              isActive
                ? 'bg-surface border border-border-subtle border-b-transparent text-txt'
                : 'border border-transparent text-txt-tertiary hover:text-txt-secondary',
              tab.comingSoon && !isActive ? 'opacity-60' : '',
            ].filter(Boolean).join(' ')}
            style={{
              marginBottom: isActive ? '-1px' : '0',
            }}
          >
            <span className="whitespace-nowrap">{tab.label}</span>
            {tab.suffix && (
              <span
                className={[
                  'ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full',
                  'text-[9px] font-semibold uppercase tracking-widest',
                  'border border-border-subtle bg-surface-alt text-txt-tertiary',
                ].join(' ')}
              >
                {tab.suffix}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
