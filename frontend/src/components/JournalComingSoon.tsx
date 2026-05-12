'use client';

import React from 'react';

export default function JournalComingSoon() {
  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden">
      <div className="px-6 py-10 sm:py-14 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-widest border border-border-subtle bg-surface-alt text-txt-tertiary mb-4">
          Coming Soon
        </div>
        <h2 className="font-secondary text-xl sm:text-2xl font-medium text-txt mb-3">
          Journal
        </h2>
        <p className="text-sm text-txt-secondary leading-relaxed mb-4">
          Track entered trades, exits, P/L, assignment outcomes, and setup quality at entry.
        </p>
        <p className="text-xs text-txt-tertiary leading-relaxed">
          The journal will let you record actual contract counts, capture base-edge score and
          RV Accel status at entry, attach exit reasons (profit target / defensive / pin risk /
          event risk), and review aggregate P&amp;L over time. Position size remains a
          trader-controlled decision — the dashboard never prescribes Full/Half/Quarter sizing.
        </p>
      </div>
    </div>
  );
}
