'use client';

import Image from 'next/image';
import ThemeToggle from './ThemeToggle';
import type { Theme } from '@/hooks/useTheme';

interface NavbarProps {
  theme: Theme;
  onToggleTheme: () => void;
  onRefresh: () => void;
  refreshing: boolean;
  onRefreshEarnings: () => void;
  earningsRefreshing: boolean;
  earningsRemaining: number;
  scannedAt: string | null;
}

export default function Navbar({ theme, onToggleTheme, onRefresh, refreshing, onRefreshEarnings, earningsRefreshing, earningsRemaining, scannedAt }: NavbarProps) {
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
  });

  // Check if scannedAt falls on today in ET
  const isFresh = (() => {
    if (!scannedAt) return false;
    const scanDate = new Date(scannedAt.replace('Z', '+00:00'));
    const todayET = new Date().toLocaleDateString('en-US', { timeZone: 'America/New_York' });
    const scanET = scanDate.toLocaleDateString('en-US', { timeZone: 'America/New_York' });
    return todayET === scanET;
  })();

  const scannedAtFormatted = scannedAt
    ? new Intl.DateTimeFormat('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: 'numeric', minute: '2-digit', timeZone: 'America/New_York', timeZoneName: 'short',
      }).format(new Date(scannedAt.replace('Z', '+00:00')))
    : '';

  return (
    <header className="h-[56px] bg-bg border-b border-border flex items-center justify-between px-6 sticky top-0 z-30">
      <div className="flex items-center gap-2.5">
        <Image src="/favicon.svg" alt="" width={24} height={24} className="rounded-[5px]" />
        <span className="font-secondary text-[17px] font-semibold text-txt">
          Theta Harvest
        </span>
      </div>

      <div className="flex items-center gap-3.5">
        <span className="font-mono text-2xs font-medium px-2.5 py-1 rounded-full text-secondary bg-secondary-subtle inline-flex items-center gap-1.5">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-secondary" />
          </span>
          Live Data
        </span>
        {isFresh && !refreshing ? (
          <span className="relative group p-1.5 rounded-md text-secondary cursor-default">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {/* Tooltip */}
            <span
              className="pointer-events-none absolute right-0 top-full mt-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top-right z-50"
              style={{ background: 'var(--color-tooltip-bg)', color: 'var(--color-tooltip-text)' }}
            >
              <span className="flex items-start gap-2.5 rounded-lg px-3.5 py-2.5 shadow-lg whitespace-nowrap" style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.18)' }}>
                <svg className="w-3.5 h-3.5 mt-0.5 shrink-0 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="flex flex-col gap-0.5">
                  <span className="text-2xs font-medium" style={{ color: 'var(--color-tooltip-text)' }}>Last Fetch:</span>
                  <span className="text-2xs" style={{ color: 'var(--color-tooltip-label)' }}>{scannedAtFormatted}</span>
                </span>
              </span>
            </span>
          </span>
        ) : (
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="p-1.5 rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors disabled:opacity-50"
            title="Refresh scan"
          >
            <svg
              className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        )}
        <span className="relative group">
          <button
            onClick={onRefreshEarnings}
            disabled={earningsRefreshing || earningsRemaining <= 0}
            className="p-1.5 rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors disabled:opacity-50"
          >
            <svg
              className={`w-3.5 h-3.5 ${earningsRefreshing ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
          </button>
          {/* Tooltip */}
          <span
            className="pointer-events-none absolute right-0 top-full mt-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top-right z-50"
            style={{ background: 'var(--color-tooltip-bg)', color: 'var(--color-tooltip-text)' }}
          >
            <span className="flex items-start gap-2.5 rounded-lg px-3.5 py-2.5 shadow-lg whitespace-nowrap" style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.18)' }}>
              <svg className="w-3.5 h-3.5 mt-0.5 shrink-0 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
              </svg>
              <span className="flex flex-col gap-0.5">
                <span className="text-2xs font-medium" style={{ color: 'var(--color-tooltip-text)' }}>Refresh earnings dates</span>
                <span className="text-2xs" style={{ color: earningsRemaining > 0 ? 'var(--color-tooltip-label)' : 'var(--color-error)' }}>
                  {earningsRemaining > 0 ? `${earningsRemaining} of 3 remaining today` : 'No refreshes remaining today'}
                </span>
              </span>
            </span>
          </span>
        </span>
        <span className="font-mono text-xs text-txt-tertiary hidden sm:block">
          {today}
        </span>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
      </div>
    </header>
  );
}
