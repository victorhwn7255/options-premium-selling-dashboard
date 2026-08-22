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


def test_safety_flag_fallback():
    """A safety-filter flag on the default model triggers ONE retry with --model sonnet;
    other errors propagate; auth errors never fall back. (2026-08-19: the v1 briefing
    corpus tripped Fable 5's AUP filter and deadlocked the log for two runs.)"""
    calls = []

    class R:
        def __init__(self, rc, out="", err=""):
            self.returncode, self.stdout, self.stderr = rc, out, err

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if "--model" in cmd:
            return R(0, out="prose from fallback")
        return R(1, err="API Error: Fable 5's safeguards flagged this message (aup)")

    real = runner.subprocess.run
    runner.subprocess.run = fake_run
    try:
        out = runner._invoke_fb("prompt text")
        _ok("fallback returned the prose", out == "prose from fallback")
        _ok("two invocations made", len(calls) == 2)
        _ok("first call had no --model (CLI default)", "--model" not in calls[0])
        i = calls[1].index("--model")
        _ok("second call pinned the fallback model", calls[1][i + 1] == runner.FALLBACK_MODEL)

        calls.clear()
        def fake_other(cmd, **kw):
            calls.append(cmd)
            return R(1, err="claude -p failed: some other error")
        runner.subprocess.run = fake_other
        try:
            runner._invoke_fb("prompt")
            raise AssertionError("expected RuntimeError")
        except RuntimeError:
            _ok("non-safety errors propagate without fallback", len(calls) == 1)

        calls.clear()
        def fake_auth(cmd, **kw):
            calls.append(cmd)
            return R(1, err="please run /login")
        runner.subprocess.run = fake_auth
        try:
            runner._invoke_fb("prompt")
            raise AssertionError("expected ClaudeAuthError")
        except runner.ClaudeAuthError:
            _ok("auth errors propagate without fallback", len(calls) == 1)
    finally:
        runner.subprocess.run = real


if __name__ == "__main__":
    print("Claude runner unit tests:")
    test_clean_notable()
    test_briefing_valid()
    test_auth_pattern_detection()
    test_safety_flag_fallback()
    print("All claude runner tests passed.")
