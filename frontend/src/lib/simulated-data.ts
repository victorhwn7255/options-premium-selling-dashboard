import type { DashboardTicker, VolHistoryPoint, TermStructurePoint2 } from './types';

// Seeded PRNG (mulberry32) — deterministic across server/client to prevent hydration mismatch
function mulberry32(seed: number) {
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// Single global seeded RNG — reset before each deterministic pass
let rng = mulberry32(42);

function seededRandom(): number {
  return rng();
}

interface RawTicker {
  sym: string;
  name: string;
  sector: string;
  price: number;
  iv: number;
  rv30: number;
  rv10: number;
  termSlope: number;
  skew25d: number;
  theta: number;
  vega: number;
  atr14: number;
  earningsDTE: number | null;
}

export const UNIVERSE: RawTicker[] = [
  { sym: "AAPL", name: "Apple Inc", sector: "Tech", price: 228.14, iv: 28.8, rv30: 16.1, rv10: 15.4, termSlope: 0.78, skew25d: 8.4, theta: -0.42, vega: 0.31, atr14: 4.82, earningsDTE: 52 },
  { sym: "META", name: "Meta Platforms", sector: "Tech", price: 612.34, iv: 34.2, rv30: 21.4, rv10: 20.9, termSlope: 0.82, skew25d: 9.1, theta: -0.68, vega: 0.48, atr14: 14.2, earningsDTE: 48 },
  { sym: "MSFT", name: "Microsoft Corp", sector: "Tech", price: 442.67, iv: 26.4, rv30: 15.6, rv10: 14.8, termSlope: 0.84, skew25d: 6.8, theta: -0.52, vega: 0.38, atr14: 8.64, earningsDTE: 55 },
  { sym: "AMZN", name: "Amazon.com", sector: "Tech", price: 214.88, iv: 30.6, rv30: 18.8, rv10: 18.4, termSlope: 0.86, skew25d: 7.2, theta: -0.38, vega: 0.28, atr14: 5.42, earningsDTE: 41 },
  { sym: "JPM", name: "JPMorgan Chase", sector: "Financials", price: 248.56, iv: 22.8, rv30: 14.4, rv10: 15.1, termSlope: 0.87, skew25d: 5.8, theta: -0.34, vega: 0.26, atr14: 5.18, earningsDTE: 38 },
  { sym: "NVDA", name: "NVIDIA Corp", sector: "Tech", price: 138.42, iv: 52.4, rv30: 39.2, rv10: 42.8, termSlope: 0.94, skew25d: 12.4, theta: -0.28, vega: 0.22, atr14: 6.42, earningsDTE: 14 },
  { sym: "TSLA", name: "Tesla Inc", sector: "Tech", price: 342.18, iv: 58.2, rv30: 44.6, rv10: 48.2, termSlope: 1.04, skew25d: 14.8, theta: -0.62, vega: 0.44, atr14: 16.8, earningsDTE: 8 },
];

function generateIVHistory(currentIV: number): number[] {
  const history: number[] = [];
  let iv = currentIV * 0.7;
  for (let i = 0; i < 252; i++) {
    iv += (seededRandom() - 0.47) * (currentIV * 0.04);
    iv = Math.max(currentIV * 0.4, Math.min(currentIV * 1.4, iv));
    history.push(+iv.toFixed(1));
  }
  return history;
}

export function generateVolHistory(ivBase: number, rvBase: number, seed = 100): VolHistoryPoint[] {
  rng = mulberry32(seed);
  const data: VolHistoryPoint[] = [];
  let iv = ivBase * 0.82;
  let rv = rvBase * 0.88;
  for (let i = 0; i < 120; i++) {
    iv += (seededRandom() - 0.46) * 1.4;
    rv += (seededRandom() - 0.48) * 0.9;
    iv = Math.max(ivBase * 0.5, Math.min(ivBase * 1.5, iv));
    rv = Math.max(rvBase * 0.5, Math.min(rvBase * 1.4, rv));
    if (i > 90) iv += 0.08;
    const d = new Date(2025, 9, 15);
    d.setDate(d.getDate() + i);
    data.push({
      date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      iv: +iv.toFixed(1),
      rv: +rv.toFixed(1),
      vrp: +(iv - rv).toFixed(1),
    });
  }
  return data;
}

export function generateTermStructure(frontIV: number, slope: number, seed = 200): TermStructurePoint2[] {
  rng = mulberry32(seed);
  const tenors = [
    { label: '1W', dte: 7 },
    { label: '2W', dte: 14 },
    { label: '1M', dte: 30 },
    { label: '2M', dte: 60 },
    { label: '3M', dte: 90 },
    { label: '6M', dte: 180 },
  ];
  return tenors.map(t => ({
    ...t,
    iv: +(frontIV * (1 - (1 - slope) * (t.dte / 180)) + (seededRandom() - 0.5) * 0.3).toFixed(1),
  }));
}

type EnrichedTicker = RawTicker & {
  vrp: number;
  rvAccel: number;
  ivPct: number;
  thetaVega: number;
  earningsWarning: boolean;
};

export function enrichData(universe: RawTicker[]): EnrichedTicker[] {
  rng = mulberry32(42); // reset seed for deterministic output
  return universe.map(t => {
    const ivHistory = generateIVHistory(t.iv);
    const ivPct = Math.round(ivHistory.filter(h => h < t.iv).length / ivHistory.length * 100);
    const vrp = +(t.iv - t.rv30).toFixed(1);
    const rvAccel = +(t.rv10 / t.rv30).toFixed(2);
    const thetaVega = +Math.abs(t.theta / t.vega).toFixed(2);
    const earningsWarning = t.earningsDTE !== null && t.earningsDTE <= 14;
    return { ...t, vrp, rvAccel, ivPct, thetaVega, earningsWarning };
  });
}
