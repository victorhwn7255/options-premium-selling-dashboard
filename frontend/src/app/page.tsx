'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import RegimeBanner from '@/components/RegimeBanner';
import Leaderboard from '@/components/Leaderboard';
import DetailPanel from '@/components/DetailPanel';
import { useTheme } from '@/hooks/useTheme';
import { buildScoredData } from '@/lib/scoring';
import { fetchLatestScan, triggerScan, refreshEarnings, fetchEarningsRemaining } from '@/lib/api';
import type { ScanResponse } from '@/lib/types';

export default function Home() {
  const { theme, toggleTheme } = useTheme();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [apiData, setApiData] = useState<ScanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [earningsRefreshing, setEarningsRefreshing] = useState(false);
  const [earningsRemaining, setEarningsRemaining] = useState<number>(3);

  // Fetch earnings remaining count on mount
  useEffect(() => {
    fetchEarningsRemaining().then(r => setEarningsRemaining(r.remaining)).catch(() => {});
  }, []);

  // Fetch real data on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const cached = await fetchLatestScan();
        if (!cancelled && cached.tickers?.length > 0) {
          setApiData(cached);
          setLoading(false);
          return;
        }
      } catch {
        // cached scan unavailable
      }

      try {
        const fresh = await triggerScan();
        if (!cancelled && fresh.tickers?.length > 0) {
          setApiData(fresh);
        }
      } catch {
        // live scan failed
      }

      if (!cancelled) setLoading(false);
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const scoredData = useMemo(() => buildScoredData(apiData), [apiData]);

  const selectedData = useMemo(
    () => scoredData.find(d => d.sym === selectedTicker) ?? null,
    [selectedTicker, scoredData]
  );

  const handleSelect = useCallback((sym: string) => {
    setSelectedTicker(prev => prev === sym ? null : sym);
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const fresh = await triggerScan();
      if (fresh.tickers?.length > 0) {
        setApiData(fresh);
      }
    } catch {
      // refresh failed — keep existing data
    }
    setRefreshing(false);
  }, []);

  const handleEarningsRefresh = useCallback(async () => {
    if (!apiData || earningsRemaining <= 0) return;
    setEarningsRefreshing(true);
    try {
      const { earnings, remaining } = await refreshEarnings();
      setEarningsRemaining(remaining);
      setApiData(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          tickers: prev.tickers.map(t => ({
            ...t,
            earnings_dte: t.ticker in earnings ? earnings[t.ticker] : t.earnings_dte,
          })),
        };
      });
    } catch {
      // keep existing data
    }
    setEarningsRefreshing(false);
  }, [apiData, earningsRemaining]);

  return (
    <div className="min-h-screen bg-bg font-primary">
      <Navbar
        theme={theme}
        onToggleTheme={toggleTheme}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        onRefreshEarnings={handleEarningsRefresh}
        earningsRefreshing={earningsRefreshing}
        earningsRemaining={earningsRemaining}
        scannedAt={apiData?.scanned_at ?? null}
      />

      <main className="max-w-[1200px] mx-auto px-6 py-5 pb-16">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-txt-tertiary">Loading market data...</p>
            </div>
          </div>
        ) : scoredData.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <p className="text-sm text-txt-secondary mb-2">No scan data available</p>
              <p className="text-xs text-txt-tertiary mb-4">
                The scanner runs automatically at 6:30 PM ET, or you can trigger a scan manually.
              </p>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="px-4 py-2 text-xs font-medium rounded-md bg-primary text-white hover:bg-primary-hover transition-colors disabled:opacity-50"
              >
                {refreshing ? 'Scanning...' : 'Run Scan Now'}
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Zone 1: Market Regime */}
            <div className="mb-5">
              <RegimeBanner data={scoredData} />
            </div>

            {/* Zone 2: Opportunity Leaderboard */}
            <div className="mb-5">
              <Leaderboard data={scoredData} selected={selectedTicker} onSelect={handleSelect} />
            </div>

            {/* Zone 3: Detail Panel */}
            <div className="mb-8">
              <DetailPanel ticker={selectedData} />
            </div>

            {/* Methodology Footer */}
            <div className="px-5 py-4 bg-surface-alt rounded-lg border border-border-subtle">
              <div className="text-xs text-txt-tertiary leading-loose">
                <strong className="text-txt-secondary">Scoring:</strong>{' '}
                VRP magnitude (0-40) + Term structure (0-25) + IV percentile (0-20) &minus; RV acceleration penalty (0-15).
                Gated by earnings proximity and backwardation.{' '}
                <strong className="text-txt-secondary">Sizing:</strong>{' '}
                Full if RV Accel &lt; 1.10, half if &lt; 1.20, quarter above.{' '}
                <span className="text-secondary">Live data — not financial advice.</span>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
