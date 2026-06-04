"""Unit tests for the Claude runner's pure-Python logic (no subprocess/quota).

Run from repo root:  python3 automation/tests/test_claude.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from automation.claude import runner  # noqa: E402


def _ok(label, cond):
    assert cond, f"FAIL {label}"
    print(f"  PASS  {label}")


def test_clean_notable():
    # accidental "**Notable:**" label stripped, intended opening bold preserved
    _ok("strips **Notable:** label, keeps bold",
        runner._clean_notable("**Notable:** **Days = 13d** rest") == "**Days = 13d** rest")
    _ok("no label -> opening bold untouched",
        runner._clean_notable("**Days = 13d new high** rest") == "**Days = 13d new high** rest")
    _ok("bare 'Notable:' stripped", runner._clean_notable("Notable: foo bar") == "foo bar")
    _ok("whitespace handled", runner._clean_notable("  **Notable:**   baz") == "baz")
    _ok("plain prose untouched", runner._clean_notable("VIX flat at 16.") == "VIX flat at 16.")


def test_briefing_valid():
    sp = {"regime_label": "THE PLAYOFFS", "tradeable_str": "3S / 3C + 1W", "avg_vrp_str": "+2.7"}
    good = ("**Regime:** THE PLAYOFFS (clean window) | **Tradeable:** 3S / 3C + 1W | "
            "**Avg VRP:** +2.7\n\nNarrative.\n\n**Position:** lean in.")
    _ok("valid briefing passes", runner._briefing_valid(good, sp) is True)
    _ok("wrong regime label fails",
        runner._briefing_valid(good.replace("THE PLAYOFFS", "THE FINALS"), sp) is False)
    _ok("altered avg VRP fails",
        runner._briefing_valid(good.replace("+2.7", "+2.8"), sp) is False)
    _ok("altered tradeable fails",
        runner._briefing_valid(good.replace("3S / 3C + 1W", "2S / 3C"), sp) is False)
    _ok("missing Position fails",
        runner._briefing_valid(good.replace("**Position:** lean in.", "done"), sp) is False)
    _ok("preamble before regime line fails",
        runner._briefing_valid("Here is the entry:\n" + good, sp) is False)


def test_auth_pattern_detection():
    _ok("detects /login", bool(runner._AUTH_PATTERNS.search("Please run /login to authenticate")))
    _ok("detects invalid api key", bool(runner._AUTH_PATTERNS.search("Invalid API key")))
    _ok("normal prose not flagged", not runner._AUTH_PATTERNS.search("QQQ is the cleanest SELL"))


if __name__ == "__main__":
    print("Claude runner unit tests:")
    test_clean_notable()
    test_briefing_valid()
    test_auth_pattern_detection()
    print("All claude runner tests passed.")
