'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import RegimeSection from './RegimeSection';

interface RegimeGuideModalProps {
  currentRegime: string;
  onClose: () => void;
}

const REGIME_DATA = [
  {
    regime: 'GARBAGE TIME',
    tagline: "Game's out of reach — sit on the bench, protect your capital",
    colorToken: 'error' as const,
    triggerLogic: 'either condition',
    triggers: [
      { metric: 'Term Slope', value: '> 1.02 (backwardation)' },
      { metric: 'Backwardation Count', value: '≥ 3 tickers' },
    ],
    explanation: [
      "The volatility term structure is inverted — front-month implied volatility exceeds back-month, meaning the market expects more turbulence now than later. This typically happens during broad selloffs, macro shocks, or cascading uncertainty (tariff escalations, credit events, pandemic scares). Multiple tickers are showing the same pattern, confirming this isn't a single-name event — it's systemic.",
      "Premium selling in backwardation is like picking up pennies in front of a bulldozer that's already moving. The options market is telling you that realized volatility will likely exceed implied — meaning you'll collect less premium than the losses your short options generate.",
    ],
    dos: [
      'Go to cash or stay fully hedged',
      'Review and tighten stops on any existing positions',
      'Study the leaderboard for post-regime opportunities — high pre-gate scores signal tickers to watch',
      'Use the time to research and plan entries for when the regime clears',
    ],
    donts: [
      'Open any new short premium positions',
      "Sell \"cheap\" puts because they look like bargains — they're cheap for a reason",
      'Try to catch the bottom by selling into the spike',
      "Assume it's temporary — regimes can persist for weeks",
    ],
    example: {
      tag: 'Feb 13, 2026',
      metrics: [
        { label: 'Avg VRP', value: '1.1' },
        { label: 'Term Slope', value: '1.09' },
        { label: 'RV Accel', value: '1.17' },
        { label: 'Tradeable', value: '1 / 25' },
      ],
      narrative:
        'Broad market in backwardation with near-zero VRP. Gold surging (GLD term slope 1.20), multiple tech names with negative VRP after selloff. Only 1 of 25 tickers passes any scoring threshold. The dashboard locks to read-only mode — the correct action is no action.',
    },
  },
  {
    regime: 'CLUTCH Q4',
    tagline: 'Every possession counts — play tight, no turnovers',
    colorToken: 'warning' as const,
    triggerLogic: 'either condition',
    triggers: [
      { metric: 'RV Accel', value: '> 1.12' },
      { metric: 'Backwardation Count', value: '≥ 1 ticker' },
    ],
    explanation: [
      'The market is playable but stressed. Either short-term realized volatility is accelerating (recent moves are bigger than the trailing average) or at least one ticker has flipped into backwardation — an early warning that broader stress may be building.',
      "Think of it as the fourth quarter of a tight playoff game. You can still score, but every play needs to be high-percentage. No hero ball. This is where defined-risk structures (spreads, iron condors) earn their keep — they cap your downside if the regime deteriorates to Garbage Time.",
    ],
    dos: [
      'Use defined-risk only — credit spreads, iron condors, iron butterflies',
      'Cut position size to Half or Quarter of normal',
      'Tighten DTE — 21-30 days max to reduce time exposure',
      'Focus on the highest-scoring tickers only (65+)',
      'Set hard exit rules before entering',
    ],
    donts: [
      'Sell naked options — undefined risk in accelerating vol is how accounts blow up',
      'Sell in tickers showing backwardation individually, even if the market-level regime is only CLUTCH Q4',
      'Add to losing positions — if a trade goes against you, take the loss',
      'Ignore the sizing chip — if it says Quarter, trade Quarter',
    ],
    example: {
      tag: 'Hypothetical',
      metrics: [
        { label: 'Ticker', value: 'AAPL' },
        { label: 'Structure', value: 'Put Spread' },
        { label: 'DTE', value: '25 days' },
        { label: 'Sizing', value: 'Half' },
      ],
      narrative:
        'AAPL scores 68 with a VRP of 9.2 and contango term structure (0.88). But RV accel is 1.14, so the regime is CLUTCH Q4. You sell a 25-DTE put credit spread at the 15-delta strike instead of a naked put, at half your normal contract count. Max loss is defined at entry.',
    },
  },
  {
    regime: 'SHOOTAROUND',
    tagline: "Running your sets — nothing weird, execute the playbook",
    colorToken: 'secondary' as const,
    triggerLogic: 'all conditions (default)',
    triggers: [
      { metric: 'Term Slope', value: '≤ 1.02 (contango)' },
      { metric: 'RV Accel', value: '≤ 1.12' },
      { metric: 'Backwardation Count', value: '= 0' },
      { metric: 'Not favorable', value: 'VRP < 8 or slope ≥ 0.90' },
    ],
    explanation: [
      "Normal conditions. The volatility term structure is in contango (back months more expensive than front months, as expected), realized vol isn't spiking, and no individual tickers are flashing warnings. The VRP exists but isn't unusually wide.",
      'This is where you spend most of your time as a premium seller — roughly 60-70% of trading days. Run your standard playbook: sell premium on high-scoring tickers at normal sizing, using whatever structures your system calls for. Nothing to get excited about, nothing to worry about.',
    ],
    dos: [
      'Execute your standard strategy on tickers scoring ≥ 50',
      'Use Full or Half sizing as indicated by the sizing chip',
      'Mix structures — strangles, spreads, and iron condors are all appropriate',
      'Target 30-45 DTE for optimal theta decay',
      'Manage winners at 50% of max profit',
    ],
    donts: [
      'Get complacent — SHOOTAROUND can transition to CLUTCH Q4 quickly',
      'Over-concentrate in one sector — spread across at least 3-4 sectors',
      "Ignore the scoring — just because the regime is normal doesn't mean every ticker is tradeable",
      'Size up beyond what the system recommends just because conditions are calm',
    ],
    example: {
      tag: 'Hypothetical',
      metrics: [
        { label: 'Ticker', value: 'QQQ' },
        { label: 'Structure', value: 'Strangle' },
        { label: 'DTE', value: '38 days' },
        { label: 'Sizing', value: 'Full' },
      ],
      narrative:
        'QQQ scores 72 with VRP of 10.4, deep contango (term slope 0.82), and stable RV accel (1.03). The regime is SHOOTAROUND with 12 of 25 tickers tradeable. You sell a 38-DTE strangle at 16-delta on both sides, Full size. Textbook premium harvest — collect theta, manage at 50% profit.',
    },
  },
  {
    regime: 'HEAT CHECK',
    tagline: "You're on fire — wide VRP in contango, keep shooting",
    colorToken: 'accent' as const,
    triggerLogic: 'both required',
    triggers: [
      { metric: 'Avg VRP', value: '> 8 vol points' },
      { metric: 'Term Slope', value: '< 0.90 (deep contango)' },
    ],
    explanation: [
      "This is the sweet spot. The options market is significantly overpricing future volatility relative to what's actually being realized — and the term structure confirms it with deep contango. The variance risk premium is fat and the market structure supports harvesting it.",
      "HEAT CHECK typically appears after a vol spike has started to resolve — IV is still elevated from the fear but realized vol has already started dropping. This is when premium sellers have the biggest statistical edge. The VRP of 8+ means implied vol is overshooting realized by 8 or more annualized vol points across the universe — historically, that level of mispricing resolves in the seller's favor roughly 85% of the time.",
    ],
    dos: [
      'Be more aggressive — this is the regime where edge is widest',
      'Use Full sizing on tickers scoring ≥ 50',
      'Consider wider strangles to capture elevated premium at further OTM strikes',
      'Extend DTE to 35-50 days to ride the IV mean-reversion',
      'Trade more tickers — when VRP is broad, diversification amplifies edge',
    ],
    donts: [
      'Go full Kelly — even in the best regime, cap at Half Kelly for ergodicity',
      "Ignore individual ticker scores — regime is favorable but not every name has edge",
      'Forget your exits — set profit targets (50-65% of max) before entering',
      "Assume it lasts forever — HEAT CHECK often transitions to SHOOTAROUND within 1-2 weeks as IV normalizes",
    ],
    example: {
      tag: 'Hypothetical',
      metrics: [
        { label: 'Ticker', value: 'AMZN' },
        { label: 'Structure', value: 'Strangle' },
        { label: 'DTE', value: '45 days' },
        { label: 'Sizing', value: 'Full' },
      ],
      narrative:
        'Market regime flips to HEAT CHECK after a vol spike subsides — avg VRP jumps to 11.2 with term slope at 0.84. AMZN scores 81 with VRP 14.8 and deep contango. You sell a 45-DTE strangle at 20-delta (wider than usual to capture the elevated premium at further strikes), Full size. The statistical edge is at its fattest — this is why you stay patient during Garbage Time.',
    },
  },
] as const;

const KEY_METRICS = [
  {
    label: 'AVG VRP',
    title: 'Volatility Risk Premium',
    desc: "The gap between what the options market thinks volatility will be (implied vol) and what it actually is (realized vol). Positive = options are overpriced, you have edge selling them. Negative = options are underpriced, selling them loses money. Measured in annualized vol points.",
  },
  {
    label: 'TERM SLOPE',
    title: 'IV Term Structure',
    desc: "The ratio of front-month IV to back-month IV. Below 1.0 = contango (normal, favorable for selling). Above 1.0 = backwardation (stressed, market expects near-term trouble). Think of it like the yield curve — inversion is a warning sign.",
  },
  {
    label: 'RV ACCEL',
    title: 'Realized Vol Acceleration',
    desc: "The ratio of short-term RV (10-day) to longer-term RV (30-day). Above 1.0 = vol is increasing. Below 1.0 = vol is decelerating. High acceleration means the market hasn't settled — even if VRP looks attractive, the ground is still shifting.",
  },
  {
    label: 'TRADEABLE',
    title: 'Tradeable Count',
    desc: "How many tickers in the non-earnings universe score above the minimum threshold. The denominator excludes earnings-gated tickers (within 14 days of reporting). A low ratio like 1/25 confirms a hostile environment; a high ratio like 18/25 signals broad opportunity.",
  },
];

export default function RegimeGuideModal({ currentRegime, onClose }: RegimeGuideModalProps) {
  const [isVisible, setIsVisible] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  // Fade in on mount
  useEffect(() => {
    requestAnimationFrame(() => setIsVisible(true));
  }, []);

  // Body scroll lock
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = prev; };
  }, []);

  // Focus close button on mount
  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  // Scroll to current regime section after transition (scoped to panel only)
  useEffect(() => {
    const timer = setTimeout(() => {
      const panel = panelRef.current;
      const el = panel?.querySelector<HTMLElement>(`[data-regime="${currentRegime}"]`);
      if (panel && el) {
        panel.scrollTop = el.offsetTop - panel.offsetTop - 24;
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [currentRegime]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  // Focus trap
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const panel = panelRef.current;
      if (!panel) return;
      const focusable = panel.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    []
  );

  // Backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  return (
    <div
      ref={overlayRef}
      onClick={handleBackdropClick}
      className={`fixed inset-0 z-[10000] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 transition-opacity duration-normal ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="Market Regime Guide"
        onKeyDown={handleKeyDown}
        className={`relative bg-surface rounded-2xl shadow-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto transition-transform duration-normal ${
          isVisible ? 'scale-100' : 'scale-95'
        }`}
      >
        {/* Sticky header */}
        <div className="sticky top-0 z-10 bg-surface border-b border-border px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="font-secondary text-2xl font-medium text-txt">
            Market Regime Guide
          </h2>
          <button
            ref={closeRef}
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors duration-fast"
            aria-label="Close"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>

        {/* Regime sections */}
        <div className="p-6 space-y-6">
          {REGIME_DATA.map((rd) => (
            <div key={rd.regime} data-regime={rd.regime}>
              <RegimeSection
                regime={rd.regime}
                tagline={rd.tagline}
                colorToken={rd.colorToken}
                triggers={[...rd.triggers]}
                triggerLogic={rd.triggerLogic}
                explanation={[...rd.explanation]}
                dos={[...rd.dos]}
                donts={[...rd.donts]}
                example={{
                  tag: rd.example.tag,
                  metrics: [...rd.example.metrics],
                  narrative: rd.example.narrative,
                }}
                isCurrent={currentRegime === rd.regime}
              />
            </div>
          ))}

          {/* Quick Reference: Key Metrics */}
          <div className="border-t border-border pt-6">
            <h3 className="font-secondary text-lg font-medium text-txt mb-4">
              Quick Reference: Key Metrics
            </h3>
            <div className="space-y-4">
              {KEY_METRICS.map((km) => (
                <div key={km.label}>
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="font-mono text-xs font-semibold text-txt">{km.label}</span>
                    <span className="text-xs text-txt-secondary">— {km.title}</span>
                  </div>
                  <p className="text-xs text-txt-secondary leading-relaxed">{km.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-border pt-5">
            <p className="text-xs text-txt-tertiary leading-relaxed italic">
              Option Harvest uses these regimes as the first decision layer — &ldquo;Should I trade today?&rdquo; — before evaluating individual tickers. The regime system is designed to keep you out of the market during the conditions that cause the worst losses in premium selling strategies. Patience during Garbage Time is what makes Heat Check profitable.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
