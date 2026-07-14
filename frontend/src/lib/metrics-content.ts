export interface MetricReading {
  label: string;
  color: 'good' | 'ok' | 'bad' | 'neutral';
}

export interface MetricDefinition {
  id: string;
  emoji: string;
  name: string;
  tag: string;
  section: 'volatility' | 'structure' | 'trade' | 'scoring' | 'v2';
  explain: string;
  analogy: string;
  formulaLabel: string;
  formulas: string[];
  readings: MetricReading[];
  /** Real dated case study from history/ — rendered as a "Real case study" box. HTML string like `analogy`. */
  example?: { tag: string; body: string };
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
    example: {
      tag: 'Jun 4, 2026',
      body:
        'XLF printed a VRP of <strong>7.3</strong> \u2014 the widest clean premium on the board \u2014 with deep contango (term slope 0.86) and a score of 74. The scanner called <strong>SELL</strong>, and the daily briefing sized it: \u201cNEW SELL, Quarter on Day-1, 30\u201345 DTE.\u201d That\u2019s the metric doing its job: a real, measured gap between what options charged and what the stock actually moved.',
    },
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
    example: {
      tag: 'Jun 10, 2026',
      body:
        'The universe\u2019s average term slope crossed above 1.0 for the first time in the logged record (<strong>1.013</strong> \u2014 net backwardation), with QQQ at 1.17 and flagged DANGER. Average VRP was just +1.1 \u2014 stress with no premium cushion. The briefing\u2019s call: <em>\u201cthis is the event, not the harvest \u2014 stay flat and let it run.\u201d</em> Backwardation days are for watching, not selling.',
    },
  },
  {
    id: 'rv-accel',
    emoji: '\uD83D\uDE80',
    name: 'RV Acceleration',
    tag: 'Environment cleanliness',
    section: 'structure',
    explain:
      'Is volatility <strong>speeding up or slowing down?</strong> We compare recent volatility (last 10 days) to the longer average (last 30 days). If the ratio is above 1.0, the market is getting <em>more</em> wild lately. If below 1.0, it\u2019s calming down. This drives the <strong>RV Stability score</strong> (0\u201315 pts) and surfaces a five-tier <strong>RV Accel Status</strong> chip on the dashboard. The status answers <em>"is the environment clean enough to sell puts?"</em> \u2014 it does <em>not</em> tell you how big to size.',
    analogy:
      'A car\u2019s speedometer vs. average speed. If you\u2019re doing 90mph right now but your trip average is 60mph, you\u2019re accelerating \u2014 the road just got bumpier. The status tells you whether the road is clean; <em>you</em> decide how fast to drive.',
    formulaLabel: 'Formula',
    formulas: ['RV Acceleration = RV10 / RV30'],
    readings: [
      { label: '\u2264 0.85 = Excellent (vol decelerating)', color: 'good' },
      { label: '0.85\u20131.00 = Good (stable to declining)', color: 'good' },
      { label: '1.00\u20131.10 = Acceptable (mildly rising)', color: 'ok' },
      { label: '1.10\u20131.20 = Caution (vol heating up)', color: 'ok' },
      { label: '> 1.20 = Avoid / Wait (vol spiking)', color: 'bad' },
    ],
    example: {
      tag: 'Jul 6, 2026',
      body:
        'Average RV acceleration re-heated to <strong>1.062</strong> and the stress broadened from 2 tickers to <strong>14 CAUTION names</strong> in a single session (stress 6.9% \u2192 48.3%) \u2014 while term structure stayed in firm contango (0.844). This is exactly what RV accel catches that the curve misses: realized vol waking up before the options market panics. Average VRP was \u22121.4; the briefing called it a <em>\u201cdefend-the-one-name tape, not a probe-for-the-window one.\u201d</em>',
    },
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
      'The <strong>final grade</strong> for each ticker \u2014 a single number from 0 to 100 that combines all the metrics above. It answers the question: <em>"Is this a good ticker to sell premium on right now?"</em> Higher is better. The score is built from VRP (is there edge?), term structure (is the market structure favorable?), IV percentile (are options expensive?), and RV acceleration (is it safe?). Two safety valves sit on top: if VRP is <strong>negative</strong>, the score is capped at 54 (can never print SELL), and if the VRP <em>ratio</em> is below 1.15, an otherwise-actionable signal is demoted to <strong>WATCHLIST</strong> \u2014 \u201cinteresting, but not enough cushion to trade.\u201d',
    analogy:
      'A player\u2019s overall rating in a video game (like NBA 2K). It combines offense, defense, speed, and shooting into one number. A 90 is a superstar. A 40 rides the bench. Same here \u2014 a score of 75 means everything lines up, a score of 30 means something\u2019s off.',
    formulaLabel: 'Formula (backend scoring)',
    formulas: [
      'VRP Quality   (0\u201330)  IV/RV ratio: 1.15\u21920, 1.60\u219230  (continuous)',
      'IV Percentile (0\u201325)  30th pctl\u21920, 100th\u219225  (continuous)',
      'Term Structure(0\u201320)  slope 0.85\u219220, 1.0\u21925, 1.15\u21920  (linear)',
      'RV Stability  (0\u201315)  accel 0.85\u219215, 1.0\u219210, 1.15\u21920  (linear)',
      'Skew          (0\u201310)  25\u0394 skew 0\u21920, 7\u219210, 12\u219210, 20\u21920  (trapezoid)',
      '\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500',
      'Total Score   = sum of all components  (clamped 0\u2013100)',
    ],
    readings: [
      { label: '\u2265 65 = SELL PREMIUM \u2014 strong edge (NORMAL regime)', color: 'good' },
      { label: '\u2265 45 = CONDITIONAL \u2014 decent edge', color: 'ok' },
      { label: '< 45 = NO EDGE \u2014 skip it', color: 'bad' },
      { label: 'CAUTION \u2192 REDUCE SIZE (\u226555) \u00b7 DANGER \u2192 AVOID, regardless of score', color: 'neutral' },
    ],
    example: {
      tag: 'Jun 4, 2026 \u2014 why you still read the flags',
      body:
        'NKE printed a score of <strong>65 (SELL)</strong> with a monster VRP of 27.3 \u2014 and the briefing flagged it <em>\u201cSCORE ARTIFACT \u2014 ignore.\u201d</em> Why? RV accel was 1.36 (Avoid/Wait \u2014 realized vol spiking) and earnings were 21 days out. The premium was \u201cwide\u201d because the market smelled real trouble. The score is doing the math, but the flags carry the context \u2014 a high score with a screaming accel status is a trap, not a trade.',
    },
  },
  {
    id: 'earnings-gate',
    emoji: '\uD83D\uDEA7',
    name: 'Earnings Gate',
    tag: 'Safety filter',
    section: 'scoring',
    explain:
      'A hard safety rule that <strong>overrides everything else.</strong> If a stock has earnings coming up within 14 days, the score is forced to 0 and the action is SKIP \u2014 no matter how good the other metrics look. Why? Because earnings announcements are like coin flips on steroids. The stock could gap 10% in either direction overnight, and that kind of move can wipe out weeks of premium-selling profits in one session. The one exemption: <strong>ETFs</strong> (SPY, QQQ, GLD, \u2026) don\u2019t report earnings, so the gate never applies to them.',
    analogy:
      'The coach benching a star player before the playoffs to avoid injury. Doesn\u2019t matter if they\u2019re playing great \u2014 the risk of losing them for the whole season isn\u2019t worth one regular-season game. Earnings are the same: the risk of one massive loss isn\u2019t worth the premium.',
    formulaLabel: 'Rule',
    formulas: [
      'if not ETF and days_to_earnings \u2264 14:',
      '    score = 0',
      '    action = "Earnings in {N}d"  (SKIP)',
      'ETFs are exempt \u2014 no earnings to gate',
    ],
    readings: [
      { label: '\u2264 14 days = gated out, score forced to 0', color: 'bad' },
      { label: '> 14 days = safe, score computed normally', color: 'good' },
    ],
  },
  {
    id: 'vol-environment-status',
    emoji: '\uD83C\uDF9A\uFE0F',
    name: 'RV Accel Status',
    tag: 'Volatility environment',
    section: 'scoring',
    explain:
      'A five-tier label \u2014 <strong>Excellent / Good / Acceptable / Caution / Avoid \u00B7 Wait</strong> \u2014 derived from RV Acceleration. It answers <em>"is the environment clean enough to sell puts?"</em>, not <em>"how much should I size?"</em> Position size is a trader-controlled decision and should be recorded in your trade journal, not prescribed by the dashboard. The status chip surfaces on the dashboard only when the environment is degraded (Caution or Avoid \u00B7 Wait). Since July 2026 the scanner also <strong>enforces</strong> this signal: RV Acceleration above 1.10 flips the ticker to CAUTION regime on its own (defined-risk only, reduced size) \u2014 a rising-RV name can no longer print SELL.',
    analogy:
      'A weather report at the trailhead. Clear, breezy, fog rolling in, storm warning, evacuation. The report tells you about conditions \u2014 <em>you</em> decide whether to hike, and how heavy a pack to carry.',
    formulaLabel: 'Logic (based on RV Acceleration)',
    formulas: [
      'if RV Acceleration \u2264 0.85 \u2192 Excellent',
      'if RV Acceleration \u2264 1.00 \u2192 Good',
      'if RV Acceleration \u2264 1.10 \u2192 Acceptable',
      'if RV Acceleration \u2264 1.20 \u2192 Caution',
      'otherwise                  \u2192 Avoid / Wait',
    ],
    readings: [
      { label: 'Excellent / Good = clean environment', color: 'good' },
      { label: 'Acceptable = trade selectively', color: 'ok' },
      { label: 'Caution / Avoid \u00B7 Wait = require strong confirmation or wait', color: 'bad' },
    ],
  },

  // \u2500\u2500 v2 \u00B7 Forward-Looking (Shadow) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  // The next-gen engine runs SILENTLY beside v1 \u2014 advisory only, changes no
  // live decision until it earns cutover with evidence. Fields visible today
  // in the MACHINE view. All thresholds [PROVISIONAL] live in backend CONFIG.
  {
    id: 'sigma-fwd',
    emoji: '\uD83D\uDD2D',
    name: 'Forward Volatility Forecast (\u03C3_fwd)',
    tag: 'v2 \u00B7 shadow',
    section: 'v2',
    explain:
      'v1 measures edge against what volatility <strong>was</strong> (RV30 \u2014 the last 30 days). v2 measures it against what volatility <strong>will likely be</strong>: \u03C3_fwd is a statistical forecast of the next 21 trading sessions, trained on 10 years of history across all 33 tickers at once. It also has a twin, <strong>\u03C3_fwd_dn</strong>, that forecasts only <em>downside</em> volatility \u2014 the kind that actually hurts a put seller. Neither changes any live decision yet \u2014 v2 runs in shadow, and you can see its numbers in the MACHINE view.',
    analogy:
      'Driving with the windshield instead of the rear-view mirror. v1 asks \u201Chow bumpy was the road behind us?\u201D; v2 looks ahead: \u201Cgiven everything we can see \u2014 recent bumps, overnight jolts, how the whole market is vibrating \u2014 how bumpy is the road <em>coming up</em>?\u201D',
    formulaLabel: 'How it forecasts (simplified)',
    formulas: [
      '\u03C3_fwd = forecast of realized vol over the next 21 sessions',
      'Inputs: smoothed daily variance (Garman-Klass + overnight gaps)',
      '        at 1/5/25/125-day memories + downside share + market factor',
      'One pooled model fit across all 33 tickers, 10y of data',
      '\u03C3_fwd_dn = same forecast, downside moves only',
    ],
    readings: [
      { label: 'The denominator of everything v2 does', color: 'neutral' },
      { label: 'Retrains from stored data on every scan', color: 'neutral' },
    ],
    example: {
      tag: 'Jul 7, 2026',
      body:
        'SBUX: v1\u2019s rear-view RV said premium looked fine, but \u03C3_fwd read <strong>0.343</strong> (34.3% annualized forward vol) \u2014 the forecast saw more turbulence coming than the trailing window did. Same option prices, different denominator, opposite conclusion. That denominator swap is the whole v2 thesis.',
    },
  },
  {
    id: 'fvrp',
    emoji: '\uD83E\uDDED',
    name: 'Forward VRP (FVRP) + z-score',
    tag: 'v2 \u00B7 shadow',
    section: 'v2',
    explain:
      'The same umbrella-overpricing idea as VRP, with one upgrade: premium is compared against the <strong>forecast</strong> (\u03C3_fwd), not the past. FVRP above 1.0 means options are charging more than the forecast says they should. The <strong>z-score</strong> then asks the sharper question: <em>\u201Cis this premium rich for THIS stock, against its own past year?\u201D</em> \u2014 a 1.06 might be dead-median for one name and exceptional for another. Below 1.0, v2 rules the name out entirely (you\u2019d be selling insurance for less than the forecast damage). Honesty note: the exact eligibility cutoffs (dead zones 1.20 index / 1.15 single-name) are <strong>[PROVISIONAL]</strong> \u2014 they get calibrated against real shadow data in Phase B before they ever gate a trade.',
    analogy:
      'Haggling at a market where you know each vendor\u2019s usual prices. $20 for a scarf might be a rip-off at one stall and a bargain at another \u2014 what matters isn\u2019t the sticker, it\u2019s the price <em>versus that vendor\u2019s own history</em>. The z-score is your memory of what this vendor usually charges.',
    formulaLabel: 'Formulas',
    formulas: [
      'FVRP = IV(30-day) / \u03C3_fwd',
      'z = how unusual today\u2019s FVRP is vs its own trailing year',
      '    (log-space, 252-day window, needs \u2265 60 observations)',
      'FVRP < 1.0 \u2192 ineligible, unconditionally (gate G4)',
    ],
    readings: [
      { label: 'z \u2265 +1 = top-of-distribution rich premium', color: 'good' },
      { label: 'z \u2248 0 = median premium \u2014 nothing special', color: 'ok' },
      { label: 'FVRP < 1.0 = negative forward edge, ruled out', color: 'bad' },
    ],
    example: {
      tag: 'Jul 7, 2026',
      body:
        'MSFT printed FVRP <strong>1.33 / z +1.62</strong> \u2014 the richest premium on the entire board \u2014 while v1\u2019s blunt CAUTION filter had it at NO EDGE. v2\u2019s forward lens surfaced real premium v1 couldn\u2019t see. The honest sequel: from Jul 8 onward v2\u2019s own gate painted MSFT DANGER and blocked it anyway \u2014 rich premium alone isn\u2019t permission. Both halves of that story are why the shadow phase exists.',
    },
  },
  {
    id: 'slope-1m3m',
    emoji: '\uD83C\uDF21\uFE0F',
    name: '1M/3M Term Slope (v2)',
    tag: 'v2 \u00B7 shadow',
    section: 'v2',
    explain:
      'v2\u2019s version of the term-structure check, tuned to be an <strong>earlier warning</strong>: it compares 1-month IV against 3-month IV (v1 compares the front against the far back of the curve). Near-term stress shows up here first. It feeds gate <strong>G2</strong> with two-sided thresholds \u2014 one level to raise the alarm, a <em>lower</em> level to stand down \u2014 so a single noisy day can\u2019t flip the state back and forth.',
    analogy:
      'A storm-warning flag on the beach. The lifeguard raises it when waves hit a trigger height, but doesn\u2019t lower it the moment one wave is calm \u2014 the sea has to stay calm below a stricter bar first. Raise fast, lower carefully.',
    formulaLabel: 'Formula + gate thresholds',
    formulas: [
      'slope_1m3m = IV(1-month) / IV(3-month)',
      'G2 CAUTION: enters \u2265 1.00, exits \u2264 0.98',
      'G2 DANGER:  enters \u2265 1.05, exits \u2264 1.02',
    ],
    readings: [
      { label: '< 0.98 = healthy near-term contango', color: 'good' },
      { label: '\u2265 1.00 = near-term stress building (CAUTION)', color: 'ok' },
      { label: '\u2265 1.05 = front-loaded fear (DANGER)', color: 'bad' },
    ],
    example: {
      tag: 'Jul 7, 2026',
      body:
        'SBUX\u2019s 1M/3M slope hit <strong>1.178</strong> \u2014 the steepest on the board \u2014 while v1 was offering a live CONDITIONAL on it. v2 vetoed: premium at dead-median (z \u22120.04) into a term structure steepening that hard is exactly the setup the gate exists to block. The veto held for six straight sessions.',
    },
  },
  {
    id: 'accel-dn',
    emoji: '\uD83D\uDCC9',
    name: 'Downside Acceleration (accel_dn)',
    tag: 'v2 \u00B7 shadow',
    section: 'v2',
    explain:
      'v1\u2019s RV Acceleration counts <strong>every</strong> big move as risk \u2014 including rallies, so a stock surging upward can look \u201Cdangerous\u201D to a put seller it\u2019s actually helping. v2 fixes the sign: accel_dn tracks only <em>down-moves</em>, comparing the last week\u2019s downside energy against the last month\u2019s. It feeds gate <strong>G3</strong> with the same raise-fast / lower-carefully thresholds as G2. A single-day crash that dominates the reading gets a special <em>transient</em> tag instead \u2014 a 3-session time-out rather than a full regime change.',
    analogy:
      'A seismograph that only records tremors, not fireworks. v1\u2019s meter jumps for both; a put seller only needs to fear the ground shaking downward.',
    formulaLabel: 'Formula + gate thresholds',
    formulas: [
      'accel_dn = \u221A( EWMA\u2085(downside var) / EWMA\u2082\u2085(downside var) )',
      'G3 CAUTION: enters \u2265 1.10, exits \u2264 1.05',
      'Single-day-spike \u2192 transient tag, 3-session blackout',
    ],
    readings: [
      { label: '< 1.0 = downside quieting', color: 'good' },
      { label: '\u2265 1.10 = downside heating up (G3 CAUTION)', color: 'bad' },
    ],
    example: {
      tag: 'Jul 9\u201310, 2026',
      body:
        'JNJ was the tempting case: rich premium (FVRP 1.17 / z +0.99) on a name v1 called AVOID. On Jul 9 v2 briefly cleared it \u2014 then accel_dn climbed <strong>1.118 \u2192 1.216</strong> and v2 re-gated it to DANGER, back in agreement with v1. The downside meter caught what the premium alone couldn\u2019t: the insurance was expensive <em>because the house was starting to shake</em>.',
    },
  },
  {
    id: 'gate-state',
    emoji: '\uD83D\uDEA6',
    name: 'v2 Gate State & Hysteresis',
    tag: 'v2 \u00B7 shadow',
    section: 'v2',
    explain:
      'v2\u2019s replacement for per-ticker regime labels: a small state machine per name \u2014 <strong>NORMAL / CAUTION / DANGER</strong> \u2014 fed by five gates: <strong>G1</strong> earnings window, <strong>G2</strong> term slope, <strong>G3</strong> downside acceleration, <strong>G4</strong> negative forward VRP (FVRP &lt; 1.0 = ruled out), and <strong>G5</strong> a book-wide freeze when the whole market\u2019s vol factor jumps. The key upgrade is <strong>hysteresis</strong>: every state change requires <em>2 consecutive sessions</em> of confirmation, and the exit bar is stricter than the entry bar \u2014 so the label can\u2019t flip-flop on one noisy day the way a threshold rule can.',
    analogy:
      'A thermostat, not a light switch. A light switch flips the instant the reading crosses the line \u2014 and chatters on a noisy signal. A thermostat waits for the temperature to <em>stay</em> different before switching, and switches back at a different level than it switched on. Same data, far fewer false starts.',
    formulaLabel: 'The machine',
    formulas: [
      'States: NORMAL \u2192 CAUTION \u2192 DANGER (+ transient tag)',
      'Any transition: 2 consecutive confirming sessions',
      'Exit thresholds tighter than entry (no flip-flopping)',
      'Gates: G1 earnings \u00B7 G2 slope \u00B7 G3 accel_dn \u00B7 G4 FVRP<1 \u00B7 G5 book freeze',
    ],
    readings: [
      { label: 'NORMAL + eligible = v2 would trade it', color: 'good' },
      { label: 'CAUTION = defined-risk territory', color: 'ok' },
      { label: 'DANGER / transient = v2 stands down', color: 'bad' },
    ],
    example: {
      tag: 'Jul 7\u201313, 2026',
      body:
        'The SBUX veto held for <strong>six consecutive sessions</strong> without a single state flip \u2014 premium stayed median, slope stayed steep, and the gate stayed shut, even as v1\u2019s label bounced between CONDITIONAL and SELL. That stability is the hysteresis working: one decision, held with confidence, instead of a new opinion every day.',
    },
  },
];

export const SECTIONS: { key: MetricDefinition['section']; label: string; desc?: string }[] = [
  { key: 'volatility', label: '\uD83D\uDCCA Volatility Metrics' },
  { key: 'structure', label: '\uD83D\uDCD0 Structure Metrics' },
  { key: 'trade', label: '\uD83D\uDD2C Trade-Level Metrics' },
  { key: 'scoring', label: '\uD83C\uDFAF Scoring & Safety' },
  {
    key: 'v2',
    label: '\uD83D\uDD2D v2 \u00B7 Forward-Looking (Shadow)',
    desc: 'The next-generation engine, running silently beside v1 since July 2026. Advisory only \u2014 it changes no live decision until it earns cutover with evidence. Its numbers are visible today in the MACHINE view.',
  },
];
