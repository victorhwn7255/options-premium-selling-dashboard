export interface MetricReading {
  label: string;
  color: 'good' | 'ok' | 'bad' | 'neutral';
}

export interface MetricDefinition {
  id: string;
  emoji: string;
  name: string;
  tag: string;
  section: 'volatility' | 'structure' | 'trade' | 'scoring';
  explain: string;
  analogy: string;
  formulaLabel: string;
  formulas: string[];
  readings: MetricReading[];
}

export const METRICS: MetricDefinition[] = [
  // ── Volatility Metrics ──────────────────────────────
  {
    id: 'rv',
    emoji: '\uD83C\uDFA2',
    name: 'Realized Volatility (RV)',
    tag: 'RV10 \u00B7 RV20 \u00B7 RV30',
    section: 'volatility',
    explain:
      'How much the stock price has <strong>actually been bouncing around</strong> recently. We measure this over different windows \u2014 the last 10 days (RV10), 20 days (RV20), and 30 days (RV30). A high number means the stock has been moving a lot. A low number means it\u2019s been chill.',
    analogy:
      'A basketball player\u2019s shooting stats from the last few games. RV10 is their stats from the last 2 games (hot streak or cold streak), RV30 is their stats from the last month (more reliable average). Both matter, but for different reasons.',
    formulaLabel: 'Formula',
    formulas: [
      'log_returns = ln(close[today] / close[yesterday])',
      'RV = stdev(log_returns, N days, ddof=1) \u00D7 \u221A252 \u00D7 100',
    ],
    readings: [
      { label: 'Low RV = calm market', color: 'neutral' },
      { label: 'High RV = wild market', color: 'neutral' },
    ],
  },
  {
    id: 'iv',
    emoji: '\uD83D\uDD2E',
    name: 'Implied Volatility (IV)',
    tag: '30-day ATM',
    section: 'volatility',
    explain:
      'How much the options market <strong>thinks</strong> the stock will bounce around over the next 30 days. It\u2019s baked into the price of options \u2014 when people are scared, they pay more for options, which pushes IV up. When things are calm, IV drops. It\u2019s basically the market\u2019s <em>fear gauge</em> for each stock.',
    analogy:
      'The Vegas odds before a game. It\u2019s a prediction \u2014 it might be right, it might be wrong. Our whole strategy is betting that this prediction is usually <em>too high</em>.',
    formulaLabel: 'How we calculate it',
    formulas: [
      '1. Find options closest to 30 days until expiry',
      '2. Find strikes within 3% of current price (ATM)',
      '3. Average the put + call IV at the nearest strike',
      '4. Interpolate between two expirations for exact 30-day value',
    ],
    readings: [
      { label: 'High IV = expensive options (good to sell)', color: 'good' },
      { label: 'Low IV = cheap options (not worth selling)', color: 'bad' },
    ],
  },
  {
    id: 'vrp',
    emoji: '\uD83D\uDCB0',
    name: 'Volatility Risk Premium (VRP)',
    tag: 'Core metric',
    section: 'volatility',
    explain:
      '<strong>The whole reason this strategy works.</strong> VRP is the gap between what the market <em>thinks</em> will happen (IV) and what <em>actually</em> happens (RV). Most of the time, IV is higher than RV \u2014 meaning people overpay for options. That overpayment is the premium we\u2019re harvesting. The bigger the gap, the more money we make selling options.',
    analogy:
      'Imagine the weather app says there\u2019s an 80% chance of a thunderstorm, so everyone buys umbrellas for $20. But it only drizzles. The umbrella sellers made bank because people <em>overpaid for protection</em>. VRP is the difference between the predicted storm and the actual drizzle.',
    formulaLabel: 'Formula',
    formulas: [
      'VRP = IV(30-day) \u2212 RV(30-day)',
      'VRP Ratio = IV(30-day) / RV(30-day)',
    ],
    readings: [
      { label: 'VRP > 8 = fat premium, strong edge', color: 'good' },
      { label: 'VRP 3\u20138 = decent edge', color: 'ok' },
      { label: 'VRP < 0 = no edge, stay away', color: 'bad' },
    ],
  },
  {
    id: 'iv-pctl',
    emoji: '\uD83D\uDCCF',
    name: 'IV Percentile & IV Rank',
    tag: '1-year lookback',
    section: 'volatility',
    explain:
      'Is today\u2019s IV high or low <strong>compared to the last year?</strong> IV Percentile tells you what percentage of days over the past year had <em>lower</em> IV than today. If it\u2019s 80, that means today\u2019s IV is higher than 80% of the past year \u2014 options are expensive. IV Rank does something similar but uses the min and max instead.',
    analogy:
      'Your height percentile at school. If you\u2019re in the 80th percentile, you\u2019re taller than 80% of kids. Same thing \u2014 if IV percentile is 80, today\u2019s volatility is higher than 80% of days this past year. We want to sell options when they\u2019re "tall" (expensive).',
    formulaLabel: 'Formulas',
    formulas: [
      'IV Percentile = (# days where IV < current) / total days \u00D7 100',
      'IV Rank = (current \u2212 min) / (max \u2212 min) \u00D7 100',
      'Lookback: 252 trading days (1 year)',
    ],
    readings: [
      { label: '\u2265 80 = options are expensive (sell!)', color: 'good' },
      { label: '40\u201380 = mid-range', color: 'ok' },
      { label: '< 40 = options are cheap (skip)', color: 'bad' },
    ],
  },

  // ── Structure Metrics ───────────────────────────────
  {
    id: 'term-structure',
    emoji: '\u26F0\uFE0F',
    name: 'Term Structure (Slope)',
    tag: 'Front IV / Back IV',
    section: 'structure',
    explain:
      'Compares IV of <strong>near-term</strong> options vs. <strong>further-out</strong> options. Normally, further-out options have higher IV (because more time = more uncertainty). That\u2019s called <em>contango</em> and it\u2019s the healthy state \u2014 the slope is below 1.0. When near-term IV becomes HIGHER than further-out IV, that\u2019s <em>backwardation</em> \u2014 the slope goes above 1.0, meaning the market is panicking about something happening <strong>right now</strong>.',
    analogy:
      'Renting an umbrella. Normally, renting one for a whole week costs more than renting for just today \u2014 more time covered, higher price. That\u2019s contango. But if renting for <em>just today</em> suddenly costs more than a whole week, it means a huge storm is expected right now and everyone\u2019s desperate for immediate protection. That\u2019s backwardation \u2014 and it\u2019s a warning sign.',
    formulaLabel: 'Formula',
    formulas: ['slope = shortest_tenor_IV / longest_tenor_IV'],
    readings: [
      { label: '< 0.90 = deep contango (great)', color: 'good' },
      { label: '0.90\u20131.00 = normal contango', color: 'ok' },
      { label: '> 1.00 = backwardation (danger)', color: 'bad' },
    ],
  },
  {
    id: 'rv-accel',
    emoji: '\uD83D\uDE80',
    name: 'RV Acceleration',
    tag: 'Speed gauge',
    section: 'structure',
    explain:
      'Is volatility <strong>speeding up or slowing down?</strong> We compare recent volatility (last 10 days) to the longer average (last 30 days). If the ratio is above 1.0, the market is getting <em>more</em> wild lately. If below 1.0, it\u2019s calming down. This drives both a <strong>scoring penalty</strong> (\u22126 pts above 1.05, \u221215 pts above 1.15) and <strong>position sizing</strong> (how big your bets should be).',
    analogy:
      'A car\u2019s speedometer vs. average speed. If you\u2019re doing 90mph right now but your trip average is 60mph, you\u2019re accelerating \u2014 things are getting riskier. We shrink our bets when acceleration is high because the road ahead might be bumpy.',
    formulaLabel: 'Formula',
    formulas: ['RV Acceleration = RV10 / RV30'],
    readings: [
      { label: '\u2264 1.10 = stable \u2192 Full size', color: 'good' },
      { label: '1.10\u20131.20 = accelerating \u2192 Half size', color: 'ok' },
      { label: '> 1.20 = spiking \u2192 Quarter size', color: 'bad' },
    ],
  },
  {
    id: 'skew',
    emoji: '\u2696\uFE0F',
    name: '25-Delta Skew',
    tag: 'Put protection demand',
    section: 'structure',
    explain:
      'Measures how much more expensive <strong>downside protection</strong> (puts) is compared to at-the-money options. When big institutions are scared of a crash, they buy more puts, which pushes skew higher. A little bit of skew is normal and healthy \u2014 it means there\u2019s steady demand for insurance, which is premium we can sell. But if skew is extreme, the smart money might know something you don\u2019t.',
    analogy:
      'Home insurance pricing. If insurance companies suddenly charge 3x more for flood insurance in your neighborhood, maybe they know something about the flood risk that you don\u2019t. Skew tells you how much the "insurance" costs relative to normal.',
    formulaLabel: 'Formula',
    formulas: [
      'skew = IV(25-delta put) \u2212 IV(ATM)',
      'Measured at nearest-to-30-DTE expiration',
    ],
    readings: [
      { label: '4\u20137 = healthy demand (good premium)', color: 'good' },
      { label: '7\u201310 = elevated (more premium, more caution)', color: 'ok' },
      { label: '> 10 = extreme (institutions hedging hard)', color: 'bad' },
    ],
  },

  // ── Trade-Level Metrics ─────────────────────────────
  {
    id: 'greeks',
    emoji: '\u231B',
    name: 'ATM Greeks: Theta & Vega',
    tag: '\u03B8 daily \u00B7 \u03BD per 1% IV',
    section: 'trade',
    explain:
      'Two numbers that tell you what\u2019s powering an option\u2019s price day to day. <strong>Theta (\u03B8)</strong> is how much money an option loses each day just from time passing \u2014 this is the premium we\u2019re collecting as sellers. <strong>Vega (\u03BD)</strong> is how much the option\u2019s price moves when IV changes by 1 point \u2014 this is our risk. We want <em>high theta</em> (more daily income) and <em>manageable vega</em> (less sensitivity to vol swings).',
    analogy:
      'Theta is the interest you earn on a savings account \u2014 money that trickles in every day just for holding the position. Vega is how much your account balance swings when the interest rate changes. You want steady drip income (theta) without wild balance swings (vega).',
    formulaLabel: 'What we show',
    formulas: [
      '\u03B8 (theta) = daily time decay in $ from the ATM option',
      '\u03BD (vega)  = price change per 1% IV move from the ATM option',
      'Both measured at nearest-to-30-DTE expiration',
    ],
    readings: [
      { label: 'High \u03B8 = more daily premium collected', color: 'good' },
      { label: 'High \u03BD = more exposure to IV swings', color: 'ok' },
    ],
  },
  {
    id: 'atr',
    emoji: '\uD83D\uDCD0',
    name: 'ATR-14 (Average True Range)',
    tag: 'Dollar movement',
    section: 'trade',
    explain:
      'The average amount (in dollars) a stock moves in a single day, measured over the last 14 days. Unlike RV which speaks in percentages, ATR speaks in <strong>actual dollars</strong>. If NVDA has an ATR of $8.50, that means it typically moves about $8.50 per day. Useful for setting stop losses and picking strike widths for credit spreads.',
    analogy:
      'How many points a team typically scores per game. If the Lakers average 112 points, you\u2019d be surprised if they scored 150 or 70. ATR is the "normal scoring range" for a stock\u2019s daily movement.',
    formulaLabel: 'Formula',
    formulas: [
      'True Range = max(high \u2212 low, |high \u2212 prev_close|, |low \u2212 prev_close|)',
      'ATR-14 = average(last 14 true ranges)',
    ],
    readings: [],
  },

  // ── Scoring & Safety ────────────────────────────────
  {
    id: 'composite-score',
    emoji: '\uD83C\uDFC6',
    name: 'Composite Score',
    tag: '0 \u2013 100',
    section: 'scoring',
    explain:
      'The <strong>final grade</strong> for each ticker \u2014 a single number from 0 to 100 that combines all the metrics above. It answers the question: <em>"Is this a good ticker to sell premium on right now?"</em> Higher is better. The score is built from VRP (is there edge?), term structure (is the market structure favorable?), IV percentile (are options expensive?), and RV acceleration (is it safe?).',
    analogy:
      'A player\u2019s overall rating in a video game (like NBA 2K). It combines offense, defense, speed, and shooting into one number. A 90 is a superstar. A 40 rides the bench. Same here \u2014 a score of 75 means everything lines up, a score of 30 means something\u2019s off.',
    formulaLabel: 'Formula (frontend scoring)',
    formulas: [
      'VRP Score     = min(40, VRP \u00D7 2.5)            \u2190 0 to 40 pts',
      'Term Score    = slope < 0.85 \u2192 25 | < 0.90 \u2192 18 | < 0.95 \u2192 12 | else \u2192 5',
      'IV Pctl Score = \u2265 80 \u2192 20 | \u2265 60 \u2192 14 | \u2265 40 \u2192 8 | else \u2192 3',
      'RV Penalty    = > 1.15 \u2192 \u221215 | > 1.05 \u2192 \u22126 | else \u2192 0',
      '\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500',
      'Total Score   = VRP + Term + IV Pctl + RV Penalty   (clamped 0\u2013100)',
    ],
    readings: [
      { label: '\u2265 70 = SELL \u2014 strong edge', color: 'good' },
      { label: '\u2265 50 = CONDITIONAL \u2014 decent edge', color: 'ok' },
      { label: '< 50 = NO EDGE \u2014 skip it', color: 'bad' },
    ],
  },
  {
    id: 'earnings-gate',
    emoji: '\uD83D\uDEA7',
    name: 'Earnings Gate',
    tag: 'Safety filter',
    section: 'scoring',
    explain:
      'A hard safety rule that <strong>overrides everything else.</strong> If a stock has earnings coming up within 14 days, the score is forced to 0 and the action is SKIP \u2014 no matter how good the other metrics look. Why? Because earnings announcements are like coin flips on steroids. The stock could gap 10% in either direction overnight, and that kind of move can wipe out weeks of premium-selling profits in one session.',
    analogy:
      'The coach benching a star player before the playoffs to avoid injury. Doesn\u2019t matter if they\u2019re playing great \u2014 the risk of losing them for the whole season isn\u2019t worth one regular-season game. Earnings are the same: the risk of one massive loss isn\u2019t worth the premium.',
    formulaLabel: 'Rule',
    formulas: [
      'if days_to_earnings \u2264 14:',
      '    score = 0',
      '    action = "Earnings in {N}d"',
      '    (skip this ticker, no exceptions)',
    ],
    readings: [
      { label: '\u2264 14 days = gated out, score forced to 0', color: 'bad' },
      { label: '> 14 days = safe, score computed normally', color: 'good' },
    ],
  },
  {
    id: 'position-sizing',
    emoji: '\uD83C\uDF9A\uFE0F',
    name: 'Position Sizing',
    tag: 'Full \u00B7 Half \u00B7 Quarter',
    section: 'scoring',
    explain:
      'How much to bet, based on how wild the market is <em>right now</em>. When recent vol is stable, you can go Full size. When it\u2019s accelerating, you shrink to Half or Quarter. This is your <strong>seatbelt</strong> \u2014 it doesn\u2019t tell you <em>what</em> to trade, it tells you <em>how much</em>.',
    analogy:
      'How hard you push in a race. Dry road? Full throttle. Wet road? Ease off. Icy road? Crawl. You still want to get there, but you adjust speed for conditions. Same thing \u2014 same trades, just different amounts.',
    formulaLabel: 'Logic (based on RV Acceleration)',
    formulas: [
      'if RV Acceleration > 1.20 \u2192 Quarter  (vol spiking)',
      'if RV Acceleration > 1.10 \u2192 Half     (vol rising)',
      'otherwise                \u2192 Full     (vol stable)',
    ],
    readings: [],
  },
];

export const SECTIONS = [
  { key: 'volatility' as const, label: '\uD83D\uDCCA Volatility Metrics' },
  { key: 'structure' as const, label: '\uD83D\uDCD0 Structure Metrics' },
  { key: 'trade' as const, label: '\uD83D\uDD2C Trade-Level Metrics' },
  { key: 'scoring' as const, label: '\uD83C\uDFAF Scoring & Safety' },
];
