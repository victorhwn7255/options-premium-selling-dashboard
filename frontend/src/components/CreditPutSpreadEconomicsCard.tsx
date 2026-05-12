'use client';

import React from 'react';
import type { CreditPutSpreadCandidate } from '@/lib/types';

interface CreditPutSpreadEconomicsCardProps {
  candidate: CreditPutSpreadCandidate;
}

/** Per-share USD formatter — never injects per-contract magic numbers here. */
function dollars(v: number, digits = 2): string {
  const sign = v < 0 ? '-' : '';
  return `${sign}$${Math.abs(v).toFixed(digits)}`;
}

/**
 * Compact 4-tile card summarising the spread economics. Used in both the
 * table-expand row and the standalone DetailPanel.
 *
 * Per-share values per build-plan §1.5. Max-loss carries an explicit
 * per-contract tooltip; everything else stays per-share.
 */
export default function CreditPutSpreadEconomicsCard({
  candidate,
}: CreditPutSpreadEconomicsCardProps) {
  const cwPct = (candidate.creditToWidth * 100).toFixed(1);
  const perContractMaxLoss = (candidate.maxLoss * 100).toFixed(0);

  const tiles = [
    {
      label: 'Net Credit',
      value: dollars(candidate.netCredit),
      sub: `per share / $${(candidate.netCredit * 100).toFixed(0)} per 1-lot`,
      tone: 'positive' as const,
    },
    {
      label: 'Max Loss',
      value: dollars(candidate.maxLoss),
      sub: `per share / $${perContractMaxLoss} per 1-lot`,
      tone: 'negative' as const,
    },
    {
      label: 'Credit / Width',
      value: `${cwPct}%`,
      sub: `width ${dollars(candidate.width, 2)}`,
      tone: candidate.creditToWidth >= 0.25 ? 'positive' : 'neutral' as const,
    },
    {
      label: 'Breakeven',
      value: dollars(candidate.breakeven),
      sub: `short ${dollars(candidate.shortPut.strike, 0)} − credit ${dollars(candidate.netCredit)}`,
      tone: 'neutral' as const,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
      {tiles.map(t => (
        <div
          key={t.label}
          className="bg-bg-alt rounded-md px-3.5 py-3 border border-border-subtle"
        >
          <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-wider uppercase mb-1">
            {t.label}
          </div>
          <div
            className="font-mono text-base font-semibold leading-tight"
            style={{
              color:
                t.tone === 'positive'
                  ? 'var(--color-secondary)'
                  : t.tone === 'negative'
                    ? 'var(--color-error)'
                    : 'var(--color-txt)',
            }}
          >
            {t.value}
          </div>
          <div className="font-primary text-[10px] text-txt-tertiary mt-0.5 leading-tight">
            {t.sub}
          </div>
        </div>
      ))}
    </div>
  );
}
