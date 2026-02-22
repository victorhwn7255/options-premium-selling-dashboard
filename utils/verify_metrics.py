#!/usr/bin/env python3
"""
Theta Harvest — Independent Metrics Verification Script.

Compares dashboard metrics against Yahoo Finance data and performs
internal consistency / reasonableness checks.

Usage:
    pip install yfinance requests numpy
    python utils/verify_metrics.py --verbose
    python utils/verify_metrics.py --tickers SPY,GOOG --api-url http://localhost:8030
"""

import argparse
import math
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import requests

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance")
    sys.exit(2)


# ── Status Enum ──────────────────────────────────────────────
class Status(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


# ── ANSI Colors ──────────────────────────────────────────────
class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

STATUS_COLOR = {
    Status.PASS: C.GREEN,
    Status.WARN: C.YELLOW,
    Status.FAIL: C.RED,
    Status.SKIP: C.DIM,
}


# ── Tolerances ───────────────────────────────────────────────
TOL_PRICE_PCT = 1.0         # 1% relative
TOL_RV_ABS = 3.0            # 3.0 vol points absolute
TOL_ATR_PCT = 5.0           # 5% relative
TOL_VRP_ABS = 0.01          # exact check
TOL_VRP_RATIO = 0.001       # exact check
TOL_RV_ACCEL = 0.002        # backend computes from unrounded intermediates
TOL_TERM_SLOPE = 0.001      # exact check
TOL_VIX_ABS = 5.0           # 5.0 vol points absolute


# ── Data Classes ─────────────────────────────────────────────
@dataclass
class CheckResult:
    name: str
    status: Status
    ours: Optional[str] = None
    ref: Optional[str] = None
    diff: Optional[str] = None
    note: Optional[str] = None


@dataclass
class TickerReport:
    ticker: str
    name: str
    price: float
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.FAIL)

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.WARN)

    @property
    def skip_count(self) -> int:
        return sum(1 for c in self.checks if c.status == Status.SKIP)


@dataclass
class FullReport:
    scan_timestamp: str
    ticker_reports: list[TickerReport] = field(default_factory=list)

    @property
    def total_checks(self) -> int:
        return sum(len(r.checks) for r in self.ticker_reports)

    @property
    def total_pass(self) -> int:
        return sum(r.pass_count for r in self.ticker_reports)

    @property
    def total_fail(self) -> int:
        return sum(r.fail_count for r in self.ticker_reports)

    @property
    def total_warn(self) -> int:
        return sum(r.warn_count for r in self.ticker_reports)

    @property
    def all_failures(self) -> list[tuple[str, CheckResult]]:
        failures = []
        for r in self.ticker_reports:
            for c in r.checks:
                if c.status == Status.FAIL:
                    failures.append((r.ticker, c))
        return failures

    @property
    def all_warnings(self) -> list[tuple[str, CheckResult]]:
        warnings = []
        for r in self.ticker_reports:
            for c in r.checks:
                if c.status == Status.WARN:
                    warnings.append((r.ticker, c))
        return warnings

    def to_dict(self) -> dict:
        """Serialize report for JSON storage."""
        def _check_dict(c: CheckResult) -> dict:
            return {
                "name": c.name,
                "status": c.status.value,
                "ours": c.ours,
                "ref": c.ref,
                "diff": c.diff,
                "note": c.note,
            }

        failures = [
            {"ticker": ticker, **_check_dict(c)}
            for ticker, c in self.all_failures
        ]
        warnings = [
            {"ticker": ticker, **_check_dict(c)}
            for ticker, c in self.all_warnings
        ]

        return {
            "scan_timestamp": self.scan_timestamp,
            "total_checks": self.total_checks,
            "pass_count": self.total_pass,
            "fail_count": self.total_fail,
            "warn_count": self.total_warn,
            "failures": failures,
            "warnings": warnings,
        }


# ── Fetching ─────────────────────────────────────────────────
def fetch_scan_data(api_url: str) -> dict:
    """GET /api/scan/latest from the backend."""
    url = f"{api_url}/api/scan/latest"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        print(f"{C.RED}ERROR: Cannot connect to backend at {api_url}{C.RESET}")
        print(f"  Make sure the backend is running: curl {api_url}/api/health")
        sys.exit(2)
    except requests.HTTPError as e:
        print(f"{C.RED}ERROR: Backend returned {e.response.status_code}{C.RESET}")
        if e.response.status_code == 404:
            print("  No scan data found. Run a scan first: POST /api/scan")
        sys.exit(2)


def fetch_yahoo_bars(tickers: list[str]) -> dict:
    """Download 6 months of OHLCV data for all tickers via yfinance.

    Uses auto_adjust=False to get raw OHLC (needed for ATR computation —
    dividend-adjusted OHLC compresses the true range).
    """
    print(f"  Downloading Yahoo Finance data for {len(tickers)} tickers...")
    data = {}
    # Batch download for efficiency
    ticker_str = " ".join(tickers)
    try:
        raw = yf.download(ticker_str, period="6mo", auto_adjust=False, progress=False)
    except Exception as e:
        print(f"{C.YELLOW}  WARN: yfinance batch download failed ({e}), falling back to individual{C.RESET}")
        raw = None

    if raw is not None and not raw.empty:
        for t in tickers:
            try:
                if len(tickers) == 1:
                    df = raw[["Close", "High", "Low"]].dropna()
                else:
                    df = raw[[("Close", t), ("High", t), ("Low", t)]].dropna()
                    df.columns = ["Close", "High", "Low"]
                if len(df) >= 15:
                    data[t] = df
            except (KeyError, TypeError):
                pass

    # Fallback for any tickers that didn't load in batch
    missing = [t for t in tickers if t not in data]
    for t in missing:
        time.sleep(0.5)
        try:
            tk = yf.Ticker(t)
            df = tk.history(period="6mo", auto_adjust=False)
            if df is not None and len(df) >= 15:
                data[t] = df[["Close", "High", "Low"]].dropna()
        except Exception:
            pass

    print(f"  Got data for {len(data)}/{len(tickers)} tickers")
    return data


def fetch_vix() -> Optional[float]:
    """Fetch latest ^VIX close from Yahoo Finance."""
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if hist is not None and len(hist) > 0:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None


def fetch_yahoo_earnings(tickers: list[str], scan_date_str: str) -> dict:
    """Fetch next earnings dates from Yahoo Finance for each ticker.

    Returns dict of {ticker: {"yahoo_date": "YYYY-MM-DD", "yahoo_dte": int}} or None per ticker.
    """
    from datetime import datetime as _dt
    scan_date = _dt.strptime(scan_date_str[:10], "%Y-%m-%d").date() if scan_date_str else __import__("datetime").date.today()
    results = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            cal = tk.calendar
            if cal is None:
                results[t] = None
                continue
            earn_date = None
            if isinstance(cal, dict):
                dates = cal.get("Earnings Date", [])
                earn_date = dates[0] if dates else None
            elif len(cal) > 0:
                earn_date = cal.iloc[0, 0]
            if earn_date and hasattr(earn_date, "date"):
                earn_date = earn_date.date()
            if earn_date and earn_date > scan_date:
                dte = (earn_date - scan_date).days
                results[t] = {"yahoo_date": earn_date.isoformat(), "yahoo_dte": dte}
            else:
                results[t] = None
        except Exception:
            results[t] = None
    return results


@dataclass
class EarningsCheckResult:
    ticker: str
    status: str  # "PASS", "FAIL", "SKIP"
    our_dte: Optional[int]
    our_date: Optional[str]
    yahoo_dte: Optional[int]
    yahoo_date: Optional[str]
    diff_days: Optional[int]
    note: Optional[str] = None


def verify_earnings(
    tickers_data: list[dict],
    yahoo_earnings: dict,
    scan_timestamp: str = "unknown",
) -> dict:
    """Verify earnings dates against Yahoo Finance.

    Returns a dict suitable for JSON storage.
    """
    from datetime import datetime as _dt, timedelta
    scan_date = _dt.strptime(scan_timestamp[:10], "%Y-%m-%d").date() if scan_timestamp and scan_timestamp != "unknown" else __import__("datetime").date.today()

    checks = []
    for td in tickers_data:
        ticker = td["ticker"]
        is_etf = td.get("is_etf", False)
        our_dte = td.get("earnings_dte")

        if is_etf:
            continue

        yahoo = yahoo_earnings.get(ticker)
        our_date = (scan_date + timedelta(days=our_dte)).isoformat() if our_dte is not None else None

        if our_dte is None and yahoo is None:
            checks.append(EarningsCheckResult(
                ticker=ticker, status="SKIP",
                our_dte=None, our_date=None,
                yahoo_dte=None, yahoo_date=None,
                diff_days=None, note="Neither source has earnings date",
            ))
            continue

        if our_dte is None and yahoo is not None:
            checks.append(EarningsCheckResult(
                ticker=ticker, status="SKIP",
                our_dte=None, our_date=None,
                yahoo_dte=yahoo["yahoo_dte"], yahoo_date=yahoo["yahoo_date"],
                diff_days=None, note="Filled from Yahoo (FMP missing)",
            ))
            continue

        if our_dte is not None and yahoo is None:
            checks.append(EarningsCheckResult(
                ticker=ticker, status="SKIP",
                our_dte=our_dte, our_date=our_date,
                yahoo_dte=None, yahoo_date=None,
                diff_days=None, note="Yahoo has no date to compare",
            ))
            continue

        diff = abs(our_dte - yahoo["yahoo_dte"])
        tol = 3 if our_dte < 30 else 7
        status = "PASS" if diff <= tol else "FAIL"

        checks.append(EarningsCheckResult(
            ticker=ticker, status=status,
            our_dte=our_dte, our_date=our_date,
            yahoo_dte=yahoo["yahoo_dte"], yahoo_date=yahoo["yahoo_date"],
            diff_days=our_dte - yahoo["yahoo_dte"],
            note=f"tolerance: {tol}d" if status == "PASS" else f"diff {diff}d exceeds tolerance {tol}d",
        ))

    total = len(checks)
    pass_count = sum(1 for c in checks if c.status == "PASS")
    fail_count = sum(1 for c in checks if c.status == "FAIL")
    skip_count = sum(1 for c in checks if c.status == "SKIP")

    return {
        "scan_timestamp": scan_timestamp,
        "total_checks": total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
        "checks": [
            {
                "ticker": c.ticker,
                "status": c.status,
                "our_dte": c.our_dte,
                "our_date": c.our_date,
                "yahoo_dte": c.yahoo_dte,
                "yahoo_date": c.yahoo_date,
                "diff_days": c.diff_days,
                "note": c.note,
            }
            for c in checks
        ],
    }


# ── Independent Computations ─────────────────────────────────
def compute_rv(closes: np.ndarray, window: int) -> float:
    """
    Realized volatility: annualized std of log returns.
    Matches calculator.py lines 82-111.
    """
    log_returns = np.diff(np.log(closes))
    if len(log_returns) < window:
        return float("nan")
    subset = log_returns[-window:]
    return float(np.std(subset, ddof=1) * math.sqrt(252) * 100)


def compute_atr14(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
    """
    14-period Average True Range (SMA, not EMA).
    Matches calculator.py lines 249-261.
    """
    true_ranges = []
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        pc = closes[i - 1]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        true_ranges.append(tr)
    if len(true_ranges) < 14:
        return float("nan")
    return sum(true_ranges[-14:]) / 14


# ── Verification Functions ───────────────────────────────────
def check_price(our_price: float, yahoo_close: float) -> CheckResult:
    """Check #1: Price within 1% of Yahoo last close."""
    if yahoo_close == 0:
        return CheckResult("Price", Status.SKIP, note="Yahoo close is 0")
    pct_diff = abs(our_price - yahoo_close) / yahoo_close * 100
    status = Status.PASS if pct_diff <= TOL_PRICE_PCT else Status.FAIL
    return CheckResult(
        name="Price",
        status=status,
        ours=f"${our_price:.2f}",
        ref=f"${yahoo_close:.2f}",
        diff=f"{pct_diff:.2f}%",
    )


def check_rv(our_rv: float, yahoo_closes: np.ndarray, window: int) -> CheckResult:
    """Check #2-4: RV within 2.0 abs vol points of Yahoo computation."""
    ref_rv = compute_rv(yahoo_closes, window)
    if math.isnan(ref_rv):
        return CheckResult(f"RV{window}", Status.SKIP, note="Insufficient Yahoo data")
    abs_diff = our_rv - ref_rv
    status = Status.PASS if abs(abs_diff) <= TOL_RV_ABS else Status.FAIL
    return CheckResult(
        name=f"RV{window}",
        status=status,
        ours=f"{our_rv:.2f}",
        ref=f"{ref_rv:.2f}",
        diff=f"{abs_diff:+.2f}",
    )


def check_atr14(our_atr: Optional[float], highs: np.ndarray, lows: np.ndarray,
                closes: np.ndarray) -> CheckResult:
    """Check #5: ATR14 within 5% of Yahoo computation."""
    if our_atr is None:
        return CheckResult("ATR14", Status.SKIP, note="Not reported by scanner")
    ref_atr = compute_atr14(highs, lows, closes)
    if math.isnan(ref_atr) or ref_atr == 0:
        return CheckResult("ATR14", Status.SKIP, note="Insufficient Yahoo data")
    pct_diff = abs(our_atr - ref_atr) / ref_atr * 100
    status = Status.PASS if pct_diff <= TOL_ATR_PCT else Status.FAIL
    return CheckResult(
        name="ATR14",
        status=status,
        ours=f"{our_atr:.2f}",
        ref=f"{ref_atr:.2f}",
        diff=f"{pct_diff:.1f}%",
    )


def check_vrp(iv_current: float, rv30: float, vrp: float) -> CheckResult:
    """Check #6: VRP == iv_current - rv30."""
    expected = round(iv_current - rv30, 2)
    diff = abs(vrp - expected)
    status = Status.PASS if diff <= TOL_VRP_ABS else Status.FAIL
    return CheckResult(
        name="VRP",
        status=status,
        ours=f"{vrp:.2f}",
        ref=f"{expected:.2f}",
        diff=f"{diff:.3f}",
        note="iv_current - rv30",
    )


def check_vrp_ratio(iv_current: float, rv30: float, vrp_ratio: float) -> CheckResult:
    """Check #7: VRP Ratio == iv_current / rv30."""
    if rv30 == 0:
        return CheckResult("VRP Ratio", Status.SKIP, note="rv30 is 0")
    expected = round(iv_current / rv30, 3)
    diff = abs(vrp_ratio - expected)
    status = Status.PASS if diff <= TOL_VRP_RATIO else Status.FAIL
    return CheckResult(
        name="VRP Ratio",
        status=status,
        ours=f"{vrp_ratio:.3f}",
        ref=f"{expected:.3f}",
        diff=f"{diff:.4f}",
        note="iv_current / rv30",
    )


def check_rv_accel(rv10: float, rv30: float, rv_accel: float) -> CheckResult:
    """Check #8: RV Accel == rv10 / rv30."""
    if rv30 == 0:
        return CheckResult("RV Accel", Status.SKIP, note="rv30 is 0")
    expected = round(rv10 / rv30, 3)
    diff = abs(rv_accel - expected)
    status = Status.PASS if diff <= TOL_RV_ACCEL else Status.FAIL
    return CheckResult(
        name="RV Accel",
        status=status,
        ours=f"{rv_accel:.3f}",
        ref=f"{expected:.3f}",
        diff=f"{diff:.4f}",
        note="rv10 / rv30",
    )


def check_term_slope(term_slope: float, term_points: list[dict]) -> CheckResult:
    """Check #9: Term Slope == front_iv / back_iv from term_structure_points."""
    if not term_points or len(term_points) < 2:
        return CheckResult("Term Slope", Status.SKIP, note="<2 term structure points")
    front_iv = term_points[0]["iv"]
    back_iv = term_points[-1]["iv"]
    if back_iv == 0:
        return CheckResult("Term Slope", Status.SKIP, note="back_iv is 0")
    expected = round(front_iv / back_iv, 3)
    diff = abs(term_slope - expected)
    status = Status.PASS if diff <= TOL_TERM_SLOPE else Status.FAIL
    return CheckResult(
        name="Term Slope",
        status=status,
        ours=f"{term_slope:.3f}",
        ref=f"{expected:.3f}",
        diff=f"{diff:.4f}",
        note=f"front({front_iv:.1f}) / back({back_iv:.1f})",
    )


def check_range(name: str, value: float, hard_min: float, hard_max: float,
                warn_min: float, warn_max: float) -> CheckResult:
    """Checks #10-13: Range / reasonableness check."""
    if value < hard_min or value > hard_max:
        return CheckResult(
            name=name, status=Status.FAIL,
            ours=f"{value:.2f}",
            diff=f"outside [{hard_min}, {hard_max}]",
        )
    if value < warn_min or value > warn_max:
        return CheckResult(
            name=name, status=Status.WARN,
            ours=f"{value:.2f}",
            diff=f"outside [{warn_min}, {warn_max}]",
        )
    return CheckResult(
        name=name, status=Status.PASS,
        ours=f"{value:.2f}",
        diff=f"in [{warn_min}, {warn_max}]",
    )


def check_spy_vix(spy_iv: float, vix_close: float) -> CheckResult:
    """Check #14: SPY IV vs CBOE VIX."""
    abs_diff = spy_iv - vix_close
    status = Status.PASS if abs(abs_diff) <= TOL_VIX_ABS else Status.FAIL
    return CheckResult(
        name="SPY IV vs VIX",
        status=status,
        ours=f"{spy_iv:.2f}",
        ref=f"{vix_close:.2f}",
        diff=f"{abs_diff:+.2f}",
        note="SPY ATM IV vs CBOE ^VIX",
    )


# ── Ticker Verification ─────────────────────────────────────
def verify_ticker(ticker_data: dict, yahoo_df) -> TickerReport:
    """Run all checks for a single ticker."""
    ticker = ticker_data["ticker"]
    name = ticker_data.get("name", ticker)
    price = ticker_data["price"]

    report = TickerReport(ticker=ticker, name=name, price=price)

    # Extract our values
    rv10 = ticker_data["rv10"]
    rv20 = ticker_data["rv20"]
    rv30 = ticker_data["rv30"]
    iv_current = ticker_data["iv_current"]
    vrp = ticker_data["vrp"]
    vrp_ratio = ticker_data["vrp_ratio"]
    rv_accel = ticker_data["rv_acceleration"]
    term_slope = ticker_data["term_slope"]
    term_points = ticker_data.get("term_structure_points", [])
    iv_rank = ticker_data["iv_rank"]
    iv_percentile = ticker_data["iv_percentile"]
    score = ticker_data["signal_score"]
    atr14 = ticker_data.get("atr14")

    # External checks (Yahoo Finance)
    if yahoo_df is not None and len(yahoo_df) >= 15:
        closes = yahoo_df["Close"].values.astype(float)
        highs = yahoo_df["High"].values.astype(float)
        lows = yahoo_df["Low"].values.astype(float)

        # #1 Price
        yahoo_close = float(closes[-1])
        report.checks.append(check_price(price, yahoo_close))

        # #2-4 RV
        report.checks.append(check_rv(rv10, closes, 10))
        report.checks.append(check_rv(rv20, closes, 20))
        report.checks.append(check_rv(rv30, closes, 30))

    else:
        for name_str in ["Price", "RV10", "RV20", "RV30"]:
            report.checks.append(CheckResult(name_str, Status.SKIP, note="No Yahoo data"))

    # Internal consistency checks
    # #6 VRP
    report.checks.append(check_vrp(iv_current, rv30, vrp))

    # #7 VRP Ratio
    report.checks.append(check_vrp_ratio(iv_current, rv30, vrp_ratio))

    # #8 RV Accel
    report.checks.append(check_rv_accel(rv10, rv30, rv_accel))

    # #9 Term Slope
    report.checks.append(check_term_slope(term_slope, term_points))

    # Range / reasonableness checks
    # #10 IV Current
    report.checks.append(check_range("IV Current", iv_current, 5, 200, 8, 150))

    # #11 IV Rank
    report.checks.append(check_range("IV Rank", iv_rank, 0, 100, 0, 100))

    # #12 IV Percentile
    report.checks.append(check_range("IV Percentile", iv_percentile, 0, 100, 0, 100))

    # #13 Score
    report.checks.append(check_range("Score", float(score), 0, 100, 0, 100))

    return report


# ── Output ───────────────────────────────────────────────────
def print_ticker_report(report: TickerReport, verbose: bool = False):
    """Print a colored table for one ticker."""
    # Header
    total = len(report.checks)
    counts = f"{report.pass_count}/{total} PASS"
    if report.fail_count:
        counts += f" | {C.RED}{report.fail_count} FAIL{C.RESET}"
    if report.warn_count:
        counts += f" | {C.YELLOW}{report.warn_count} WARN{C.RESET}"
    if report.skip_count:
        counts += f" | {C.DIM}{report.skip_count} SKIP{C.RESET}"

    if not verbose and report.fail_count == 0 and report.warn_count == 0:
        # Compact one-liner for clean tickers
        print(f"  {C.GREEN}PASS{C.RESET}  {report.ticker:<6} {report.name:<25} {counts}")
        return

    # Full table
    print()
    print(f"{'=' * 60}")
    print(f"  {C.BOLD}{report.ticker}{C.RESET}  {report.name}  |  Price: ${report.price:.2f}")
    print(f"{'-' * 60}")
    print(f"  {'Metric':<14} {'Ours':>10} {'Ref':>10} {'Diff':>10} {'Status':>8}")
    print(f"  {'─' * 54}")

    for check in report.checks:
        if not verbose and check.status == Status.PASS:
            continue
        color = STATUS_COLOR[check.status]
        ours = check.ours or "—"
        ref = check.ref or "—"
        diff = check.diff or "—"
        status_str = f"{color}{check.status.value}{C.RESET}"
        print(f"  {check.name:<14} {ours:>10} {ref:>10} {diff:>10} {status_str:>17}")
        if check.note and verbose:
            print(f"  {C.DIM}  └ {check.note}{C.RESET}")

    print(f"  {'─' * 54}")
    print(f"  Result: {counts}")


def print_summary(report: FullReport):
    """Print the final summary."""
    print()
    print(f"{'=' * 60}")
    print(f"  {C.BOLD}VERIFICATION SUMMARY{C.RESET}")
    print(f"{'-' * 60}")
    print(f"  Scan: {report.scan_timestamp}")
    print(f"  Tickers: {len(report.ticker_reports)}")

    total = report.total_checks
    pass_c = report.total_pass
    fail_c = report.total_fail
    warn_c = report.total_warn

    status_line = f"  Total: {total} checks — {C.GREEN}{pass_c} PASS{C.RESET}"
    if warn_c:
        status_line += f", {C.YELLOW}{warn_c} WARN{C.RESET}"
    if fail_c:
        status_line += f", {C.RED}{fail_c} FAIL{C.RESET}"
    print(status_line)

    # List failures
    failures = report.all_failures
    if failures:
        print()
        print(f"  {C.RED}Failures:{C.RESET}")
        for ticker, check in failures:
            ours = check.ours or "?"
            ref = check.ref or "?"
            diff_str = f"  ({check.diff})" if check.diff else ""
            print(f"    {ticker:<6} {check.name:<14} {ours} vs {ref}{diff_str}")

    # List warnings (compact)
    warned = []
    for r in report.ticker_reports:
        for c in r.checks:
            if c.status == Status.WARN:
                warned.append((r.ticker, c))
    if warned:
        print()
        print(f"  {C.YELLOW}Warnings:{C.RESET}")
        for ticker, check in warned:
            note = check.note or check.diff or ""
            print(f"    {ticker:<6} {check.name:<14} {check.ours or '?'} — {note}")

    print(f"{'=' * 60}")


# ── Library Entry Point (for in-process use) ────────────────
def verify_all(
    tickers_data: list[dict],
    yahoo_data: dict,
    vix_close: Optional[float],
    scan_timestamp: str = "unknown",
) -> FullReport:
    """Run all verification checks given pre-fetched data.

    Args:
        tickers_data: List of ticker dicts from scan results.
        yahoo_data: Dict of {ticker: DataFrame} from fetch_yahoo_bars().
        vix_close: Latest ^VIX close, or None.
        scan_timestamp: ISO timestamp of the scan being verified.

    Returns:
        FullReport with all check results.
    """
    report = FullReport(scan_timestamp=scan_timestamp)

    for td in tickers_data:
        ticker = td["ticker"]
        yahoo_df = yahoo_data.get(ticker)
        ticker_report = verify_ticker(td, yahoo_df)

        if ticker == "SPY" and vix_close is not None:
            ticker_report.checks.append(check_spy_vix(td["iv_current"], vix_close))

        report.ticker_reports.append(ticker_report)

    return report


# ── Orchestration ────────────────────────────────────────────
def run_all(api_url: str, ticker_filter: Optional[list[str]], verbose: bool) -> int:
    """Main orchestration. Returns exit code."""
    print(f"{C.BOLD}Theta Harvest — Metrics Verification{C.RESET}")
    print(f"  Backend: {api_url}")
    print()

    # 1. Fetch scan data
    print("  Fetching scan data from backend...")
    scan_data = fetch_scan_data(api_url)
    tickers_data = scan_data.get("tickers", [])
    scan_ts = scan_data.get("timestamp", scan_data.get("scanned_at", "unknown"))

    if not tickers_data:
        print(f"{C.RED}ERROR: No tickers in scan data{C.RESET}")
        return 2

    # Filter tickers if requested
    if ticker_filter:
        filter_upper = [t.upper() for t in ticker_filter]
        tickers_data = [t for t in tickers_data if t["ticker"] in filter_upper]
        if not tickers_data:
            print(f"{C.RED}ERROR: None of the requested tickers found in scan{C.RESET}")
            return 2

    ticker_symbols = [t["ticker"] for t in tickers_data]
    print(f"  Scan timestamp: {scan_ts}")
    print(f"  Tickers to verify: {len(ticker_symbols)}")
    print()

    # 2. Fetch Yahoo data
    yahoo_data = fetch_yahoo_bars(ticker_symbols)

    # 3. Fetch VIX for SPY cross-check
    vix_close = None
    if "SPY" in ticker_symbols:
        print("  Fetching ^VIX for SPY cross-check...")
        vix_close = fetch_vix()
        if vix_close:
            print(f"  VIX last close: {vix_close:.2f}")
        else:
            print(f"  {C.YELLOW}WARN: Could not fetch VIX data{C.RESET}")
    print()

    # 4. Verify each ticker
    report = FullReport(scan_timestamp=scan_ts)

    print(f"  {C.BOLD}Running checks...{C.RESET}")
    if not verbose:
        print()

    for td in tickers_data:
        ticker = td["ticker"]
        yahoo_df = yahoo_data.get(ticker)
        ticker_report = verify_ticker(td, yahoo_df)

        # Add SPY-specific VIX check
        if ticker == "SPY" and vix_close is not None:
            ticker_report.checks.append(check_spy_vix(td["iv_current"], vix_close))

        report.ticker_reports.append(ticker_report)
        print_ticker_report(ticker_report, verbose=verbose)

    # 5. Summary
    print_summary(report)

    # Exit code
    if report.total_fail > 0:
        return 1
    return 0


# ── CLI ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Verify Theta Harvest metrics against Yahoo Finance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python utils/verify_metrics.py --verbose
  python utils/verify_metrics.py --tickers SPY,GOOG,AAPL
  python utils/verify_metrics.py --api-url http://localhost:8030 --verbose
        """,
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated list of tickers to verify (default: all)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8030",
        help="Backend API URL (default: http://localhost:8030)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all checks including PASS (default: only FAIL/WARN)",
    )
    args = parser.parse_args()

    ticker_filter = None
    if args.tickers:
        ticker_filter = [t.strip() for t in args.tickers.split(",") if t.strip()]

    try:
        exit_code = run_all(args.api_url, ticker_filter, args.verbose)
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Interrupted{C.RESET}")
        exit_code = 2
    except Exception as e:
        print(f"\n{C.RED}ERROR: {e}{C.RESET}")
        exit_code = 2

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
