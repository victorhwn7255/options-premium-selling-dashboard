'use client';

import { useState } from 'react';
import Image from 'next/image';
import ThemeToggle from './ThemeToggle';
import ExplainMetricsModal from './ExplainMetricsModal';
import type { Theme } from '@/hooks/useTheme';

interface NavbarProps {
  theme: Theme;
  onToggleTheme: () => void;
  onRefresh: () => void;
  refreshing: boolean;
  scanProgress: string | null;
  onRefreshEarnings: () => void;
  earningsRefreshing: boolean;
  earningsRemaining: number;
  scannedAt: string | null;
  onOpenRegimeGuide: () => void;
}

export default function Navbar({ theme, onToggleTheme, onRefresh, refreshing, scanProgress, onRefreshEarnings, earningsRefreshing, earningsRemaining, scannedAt, onOpenRegimeGuide }: NavbarProps) {
  const [metricsModalOpen, setMetricsModalOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

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

  // Check if today is a non-trading day in ET (weekend or US market holiday)
  // Non-trading day: weekends + holidays (clock icon)
  const isNonTradingDay = (() => {
    const now = new Date();
    const etStr = now.toLocaleDateString('en-US', { timeZone: 'America/New_York', weekday: 'short', year: 'numeric', month: '2-digit', day: '2-digit' });
    const weekday = etStr.split(',')[0];
    if (weekday === 'Sat' || weekday === 'Sun') return true;
    const etDate = new Date(now.toLocaleDateString('en-US', { timeZone: 'America/New_York' }));
    const y = etDate.getFullYear(), m = etDate.getMonth(), d = etDate.getDate();
    const nthWeekday = (month: number, wday: number, n: number) => {
      const first = new Date(y, month, 1);
      const offset = (wday - first.getDay() + 7) % 7;
      return 1 + offset + 7 * (n - 1);
    };
    const lastMonday = (month: number) => {
      const last = new Date(y, month + 1, 0);
      const offset = (last.getDay() - 1 + 7) % 7;
      return last.getDate() - offset;
    };
    const observe = (month: number, day: number) => {
      const dt = new Date(y, month, day);
      const dow = dt.getDay();
      if (dow === 6) return { m: month, d: day - 1 };
      if (dow === 0) return { m: month, d: day + 1 };
      return { m: month, d: day };
    };
    const a = y % 19, b = Math.floor(y / 100), c = y % 100;
    const dd = Math.floor(b / 4), e = b % 4;
    const f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - dd - g + 15) % 30;
    const i = Math.floor(c / 4), k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const mm = Math.floor((a + 11 * h + 22 * l) / 451);
    const easterMonth = Math.floor((h + l - 7 * mm + 114) / 31) - 1;
    const easterDay = ((h + l - 7 * mm + 114) % 31) + 1;
    const goodFriday = new Date(y, easterMonth, easterDay - 2);
    const holidays: { m: number; d: number }[] = [
      observe(0, 1),                            // New Year's
      { m: 0, d: nthWeekday(0, 1, 3) },         // MLK Day
      { m: 1, d: nthWeekday(1, 1, 3) },         // Presidents' Day
      { m: goodFriday.getMonth(), d: goodFriday.getDate() }, // Good Friday
      { m: 4, d: lastMonday(4) },                // Memorial Day
      observe(5, 19),                            // Juneteenth
      observe(6, 4),                             // Independence Day
      { m: 8, d: nthWeekday(8, 1, 1) },         // Labor Day
      { m: 10, d: nthWeekday(10, 4, 4) },       // Thanksgiving
      observe(11, 25),                           // Christmas
    ];
    return holidays.some(h => h.m === m && h.d === d);
  })();

  // Market closed: non-trading day OR outside market hours (for badge display)
  const isMarketClosed = (() => {
    if (isNonTradingDay) return true;
    const now = new Date();
    const etTime = now.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour12: false, hour: '2-digit', minute: '2-digit' });
    const [hours, minutes] = etTime.split(':').map(Number);
    const minutesSinceMidnight = hours * 60 + minutes;
    return minutesSinceMidnight < 570 || minutesSinceMidnight >= 960; // 9:30=570, 16:00=960
  })();

  // Check if scan window is open (trading day, after 6:30 PM ET)
  const isScanWindowOpen = (() => {
    if (isNonTradingDay) return false;
    const now = new Date();
    const etTime = now.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour12: false, hour: '2-digit', minute: '2-digit' });
    const [hours, minutes] = etTime.split(':').map(Number);
    return hours > 18 || (hours === 18 && minutes >= 30);
  })();

  const scannedAtFormatted = scannedAt
    ? new Intl.DateTimeFormat('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: 'numeric', minute: '2-digit', timeZone: 'America/New_York', timeZoneName: 'short',
      }).format(new Date(scannedAt.replace('Z', '+00:00')))
    : '';

  return (
    <header className="h-[56px] bg-bg border-b border-border sticky top-0 z-30 relative">
      {/* Logo — pinned to viewport left */}
      <div className="absolute left-4 sm:left-6 top-0 h-[56px] flex items-center gap-2.5">
        <Image src="/favicon.svg" alt="" width={24} height={24} className="rounded-[5px]" />
        <span className="font-secondary text-[17px] font-semibold text-txt hidden sm:inline">
          Theta Harvest
        </span>
      </div>

      {/* Content-aligned container */}
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
        {/* Left: Explain buttons (desktop only) */}
        <div className="hidden sm:flex items-center gap-2 ml-44 2xl:ml-0">
          <button
            onClick={onOpenRegimeGuide}
            className="font-primary text-sm font-medium text-txt-tertiary hover:text-txt bg-surface-alt hover:bg-surface-raised px-3 py-1.5 rounded-md transition-colors duration-fast"
          >
            Explain Market Regime
          </button>
          <button
            onClick={() => setMetricsModalOpen(true)}
            className="font-primary text-sm font-medium text-txt-tertiary hover:text-txt bg-surface-alt hover:bg-surface-raised px-3 py-1.5 rounded-md transition-colors duration-fast"
          >
            Explain Metrics
          </button>
        </div>

        {/* Right side */}
        <div className="ml-auto flex items-center gap-2 sm:gap-3.5">
          {/* Market status badge (desktop only) */}
          <span className={`font-mono text-xs font-medium px-2.5 py-1 rounded-full hidden sm:inline-flex items-center gap-1.5 ${
            isMarketClosed ? 'text-error bg-error-subtle' : 'text-secondary bg-secondary-subtle'
          }`}>
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isMarketClosed ? 'bg-error' : 'bg-secondary'}`} />
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isMarketClosed ? 'bg-error' : 'bg-secondary'}`} />
            </span>
            {isMarketClosed ? 'Market Closed' : 'Live Data'}
          </span>

          {/* Scan status (desktop only) */}
          <div className="hidden sm:block">
            {isNonTradingDay && !refreshing ? (
              <span className="relative group p-1.5 cursor-default" style={{ color: '#d4768a' }}>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
                {/* Tooltip */}
                <span
                  className="pointer-events-none absolute right-0 top-full mt-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top-right z-50"
                  style={{ background: 'var(--color-tooltip-bg)', color: 'var(--color-tooltip-text)' }}
                >
                  <span className="flex items-start gap-2.5 rounded-lg px-3.5 py-2.5 shadow-lg whitespace-nowrap" style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.18)' }}>
                    <span className="flex flex-col gap-0.5">
                      <span className="text-2xs font-medium" style={{ color: 'var(--color-tooltip-text)' }}>Market closed</span>
                      <span className="text-2xs" style={{ color: 'var(--color-tooltip-label)' }}>Showing data from {scannedAtFormatted}</span>
                    </span>
                  </span>
                </span>
              </span>
            ) : isFresh && !refreshing ? (
              <span className="relative group p-1.5 rounded-md text-secondary cursor-default">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
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
            ) : !isScanWindowOpen && !refreshing ? (
              <span className="relative group p-1.5 rounded-md cursor-default text-txt-tertiary">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
                {/* Tooltip */}
                <span
                  className="pointer-events-none absolute right-0 top-full mt-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top-right z-50"
                  style={{ background: 'var(--color-tooltip-bg)', color: 'var(--color-tooltip-text)' }}
                >
                  <span className="flex items-start gap-2.5 rounded-lg px-3.5 py-2.5 shadow-lg whitespace-nowrap" style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.18)' }}>
                    <span className="flex flex-col gap-0.5">
                      <span className="text-2xs font-medium" style={{ color: 'var(--color-tooltip-text)' }}>Fetch available after 6:30 PM ET</span>
                      {scannedAtFormatted && <span className="text-2xs" style={{ color: 'var(--color-tooltip-label)' }}>Showing data from {scannedAtFormatted}</span>}
                    </span>
                  </span>
                </span>
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <button
                  onClick={onRefresh}
                  disabled={refreshing}
                  className="p-1.5 rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors disabled:opacity-50"
                  title="Fetch latest data"
                >
                  <svg
                    className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
                {refreshing && scanProgress && (
                  <span className="font-mono text-xs text-txt-tertiary">{scanProgress}</span>
                )}
              </span>
            )}
          </div>

          {/* Earnings refresh (desktop only) */}
          <span className="relative group hidden sm:block">
            <button
              onClick={onRefreshEarnings}
              disabled={earningsRefreshing || earningsRemaining <= 0}
              className="p-1.5 rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors disabled:opacity-50"
            >
              <svg
                className={`w-5 h-5 ${earningsRefreshing ? 'animate-spin' : ''}`}
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
                    {earningsRemaining > 0 ? `${earningsRemaining} of 1 remaining today` : 'No refreshes remaining today'}
                  </span>
                </span>
              </span>
            </span>
          </span>

          {/* Date (desktop only) */}
          <span className="font-mono text-sm text-txt-tertiary hidden sm:block">
            {today}
          </span>

          {/* ThemeToggle — always visible */}
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />

          {/* Hamburger button (mobile only) */}
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="sm:hidden p-2 rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors"
          >
            {menuOpen ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <div className="sm:hidden absolute top-[56px] left-0 right-0 bg-bg border-b border-border shadow-md z-40 px-4 py-3 space-y-3">
          {/* Row 1: Text buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => { onOpenRegimeGuide(); setMenuOpen(false); }}
              className="font-primary text-xs font-medium text-txt-tertiary hover:text-txt bg-surface-alt hover:bg-surface-raised px-3 py-2 rounded-md transition-colors duration-fast"
            >
              Explain Market Regime
            </button>
            <button
              onClick={() => { setMetricsModalOpen(true); setMenuOpen(false); }}
              className="font-primary text-xs font-medium text-txt-tertiary hover:text-txt bg-surface-alt hover:bg-surface-raised px-3 py-2 rounded-md transition-colors duration-fast"
            >
              Explain Metrics
            </button>
          </div>
          {/* Row 2: Status + actions */}
          <div className="flex items-center justify-between">
            <span className={`font-mono text-2xs font-medium px-2.5 py-1 rounded-full inline-flex items-center gap-1.5 ${
              isMarketClosed ? 'text-error bg-error-subtle' : 'text-secondary bg-secondary-subtle'
            }`}>
              <span className="relative flex h-1.5 w-1.5">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isMarketClosed ? 'bg-error' : 'bg-secondary'}`} />
                <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${isMarketClosed ? 'bg-error' : 'bg-secondary'}`} />
              </span>
              {isMarketClosed ? 'Market Closed' : 'Live Data'}
            </span>
            <div className="flex items-center gap-2">
              {isNonTradingDay && !refreshing ? (
                <span className="p-2 cursor-default" style={{ color: '#d4768a' }}>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                </span>
              ) : isFresh && !refreshing ? (
                <span className="p-2 rounded-md text-secondary cursor-default">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              ) : !isScanWindowOpen && !refreshing ? (
                <span className="p-2 rounded-md cursor-default text-txt-tertiary">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <button
                    onClick={() => { onRefresh(); setMenuOpen(false); }}
                    disabled={refreshing}
                    className="p-2 rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors disabled:opacity-50"
                    title="Fetch latest data"
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
                  {refreshing && scanProgress && (
                    <span className="font-mono text-2xs text-txt-tertiary">{scanProgress}</span>
                  )}
                </span>
              )}
              <button
                onClick={() => { onRefreshEarnings(); setMenuOpen(false); }}
                disabled={earningsRefreshing || earningsRemaining <= 0}
                className="p-2 rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors disabled:opacity-50"
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
            </div>
          </div>
          {/* Row 3: Date */}
          <span className="font-mono text-xs text-txt-tertiary">{today}</span>
        </div>
      )}

      <ExplainMetricsModal open={metricsModalOpen} onClose={() => setMetricsModalOpen(false)} />
    </header>
  );
}
