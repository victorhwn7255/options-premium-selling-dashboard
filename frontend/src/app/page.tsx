'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import RegimeBanner, { computeRegime } from '@/components/RegimeBanner';
import RegimeGuideModal from '@/components/RegimeGuideModal';
import Leaderboard from '@/components/Leaderboard';
import { useTheme } from '@/hooks/useTheme';
import { buildScoredData } from '@/lib/scoring';
import { fetchLatestScan, triggerScan, refreshEarnings, fetchEarningsRemaining, fetchScanStatus, fetchVerificationLatest, fetchEarningsVerificationLatest, fetchComparison } from '@/lib/api';
import type { ScanResponse, VerificationResult, EarningsVerificationResult, TickerDelta } from '@/lib/types';

export default function Home() {
  const { theme, toggleTheme } = useTheme();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [apiData, setApiData] = useState<ScanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [scanProgress, setScanProgress] = useState<string | null>(null);
  const [earningsRefreshing, setEarningsRefreshing] = useState(false);
  const [earningsRemaining, setEarningsRemaining] = useState<number>(1);
  const [regimeGuideOpen, setRegimeGuideOpen] = useState(false);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [earningsVerification, setEarningsVerification] = useState<EarningsVerificationResult | null>(null);
  const [deltaMap, setDeltaMap] = useState<Record<string, TickerDelta>>({});

  // Fetch earnings remaining count + verification status on mount
  useEffect(() => {
    fetchEarningsRemaining().then(r => setEarningsRemaining(r.remaining)).catch(() => {});
    fetchVerificationLatest().then(v => setVerification(v)).catch(() => {});
    fetchEarningsVerificationLatest().then(v => setEarningsVerification(v)).catch(() => {});
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

  // Fetch day-over-day comparison (non-critical, silent fail)
  useEffect(() => {
    if (!apiData?.tickers?.length) return;
    fetchComparison()
      .then(comp => {
        const map: Record<string, TickerDelta> = {};
        for (const tc of comp.tickers) {
          if (tc.deltas) map[tc.ticker] = tc.deltas;
        }
        setDeltaMap(map);
      })
      .catch(() => {});
  }, [apiData?.scanned_at]); // eslint-disable-line react-hooks/exhaustive-deps

  const scoredData = useMemo(() => buildScoredData(apiData), [apiData]);
  const currentRegime = useMemo(() => computeRegime(scoredData).regime, [scoredData]);

  const selectedData = useMemo(
    () => scoredData.find(d => d.sym === selectedTicker) ?? null,
    [selectedTicker, scoredData]
  );

  const handleSelect = useCallback((sym: string) => {
    setSelectedTicker(prev => prev === sym ? null : sym);
  }, []);

  // Poll scan progress while refreshing
  useEffect(() => {
    if (!refreshing) { setScanProgress(null); return; }
    const interval = setInterval(async () => {
      try {
        const status = await fetchScanStatus();
        if (status.status === 'scanning' && status.total > 0) {
          setScanProgress(`${status.current}/${status.total} — ${status.ticker}`);
        }
      } catch { /* ignore */ }
    }, 3000);
    return () => clearInterval(interval);
  }, [refreshing]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    setScanProgress(null);
    try {
      const fresh = await triggerScan();
      if (fresh.tickers?.length > 0) {
        setApiData(fresh);
      }
      // Verification runs as background task after scan — poll for it
      setTimeout(async () => {
        let metricsFound = false;
        let earningsFound = false;
        for (let i = 0; i < 12; i++) {
          await new Promise(r => setTimeout(r, 10000));
          try {
            if (!metricsFound) {
              const v = await fetchVerificationLatest();
              if (v && v.scanned_at === fresh.scanned_at) { setVerification(v); metricsFound = true; }
            }
            if (!earningsFound) {
              const ev = await fetchEarningsVerificationLatest();
              if (ev && ev.scanned_at === fresh.scanned_at) { setEarningsVerification(ev); earningsFound = true; }
            }
            if (metricsFound && earningsFound) break;
          } catch { /* ignore */ }
        }
      }, 5000);
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
            earnings_dte: (t.ticker in earnings && earnings[t.ticker] !== null) ? earnings[t.ticker] : t.earnings_dte,
          })),
        };
      });
    } catch {
      // keep existing data
    }
    setEarningsRefreshing(false);
  }, [apiData, earningsRemaining]);

  return (
    <div className="min-h-screen bg-white font-body">
      <Navbar
        theme={theme}
        onToggleTheme={toggleTheme}
        onRefresh={handleRefresh}
        scanProgress={scanProgress}
        refreshing={refreshing}
        onRefreshEarnings={handleEarningsRefresh}
        earningsRefreshing={earningsRefreshing}
        earningsRemaining={earningsRemaining}
        scannedAt={apiData?.scanned_at ?? null}
        verification={verification}
        earningsVerification={earningsVerification}
        onOpenRegimeGuide={() => setRegimeGuideOpen(true)}
      />

      <main className="max-w-[1152px] mx-auto px-6 md:px-8 py-6 pb-16">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="w-6 h-6 border-2 border-black border-t-transparent animate-spin mx-auto mb-3" />
              <p className="text-sm text-[#525252] font-mono uppercase tracking-widest">Loading market data...</p>
            </div>
          </div>
        ) : scoredData.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <p className="text-sm text-[#525252] mb-2 font-body">No scan data available</p>
              <p className="text-xs text-[#525252] mb-4 font-body">
                Data is fetched automatically at 6:30 PM ET, or you can fetch it manually.
              </p>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="px-8 py-4 font-mono text-xs font-medium uppercase tracking-widest bg-black text-white border-2 border-black hover:bg-white hover:text-black transition-none disabled:opacity-50"
              >
                {refreshing ? 'Fetching...' : 'Fetch Latest Data \u2192'}
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Zone 1: Market Regime */}
            <div className="mb-6">
              <RegimeBanner data={scoredData} />
            </div>

            <hr className="border-0 border-t-4 border-black mb-6" />

            {/* Zone 2: Opportunity Leaderboard (detail expands inline) */}
            <div className="mb-6">
              <Leaderboard data={scoredData} selected={selectedTicker} onSelect={handleSelect} selectedData={selectedData} deltaMap={deltaMap} />
            </div>

            <hr className="border-0 border-t-4 border-black mb-6" />

            {/* Methodology Footer */}
            <div className="px-6 py-5 bg-[#F5F5F5] border-t-4 border-black">
              <div className="text-xs text-[#525252] leading-loose font-body">
                <strong className="text-black">Scoring:</strong>{' '}
                VRP quality (0-30) + IV percentile (0-25) + Term structure (0-20) + RV stability (0-15) + Skew (0-10).
                Gated by earnings proximity and negative VRP.{' '}
                <strong className="text-black">Sizing:</strong>{' '}
                Full if RV Accel &lt; 1.10, half if &lt; 1.20, quarter above.{' '}
                <span className="font-mono uppercase tracking-widest">Live data — not financial advice.</span>
              </div>
            </div>
          </>
        )}
      </main>

      {regimeGuideOpen && (
        <RegimeGuideModal currentRegime={currentRegime} onClose={() => setRegimeGuideOpen(false)} />
      )}
    </div>
  );
}
