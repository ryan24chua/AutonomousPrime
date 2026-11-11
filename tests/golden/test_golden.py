"""Golden master: today's dry-run outcomes must not change unless a commit means them to.

It pins plans, costs, metrics, scores, votes, rule ids, outcomes and round counts, not prose (see capture.py).
If this fails after a pure refactor, the refactor changed behaviour: fix the code, not the snapshot.
If the change is intended, land it as its own commit: run `python -m tests.golden.update` and say in the
commit message which numbers moved and why.
"""

import difflib
import json

from tests.golden.capture import SNAPSHOT, capture


def _lines(obj) -> list[str]:
    return json.dumps(obj, indent=1, sort_keys=True).splitlines()


def test_dry_run_outputs_match_snapshot():
    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    actual = capture()
    if actual != expected:
        diff = list(difflib.unified_diff(_lines(expected), _lines(actual), "snapshot", "current", n=2, lineterm=""))
        shown = "\n".join(diff[:200])
        raise AssertionError(f"Golden master changed ({len(diff)} diff lines, first 200 shown):\n{shown}")


def test_projection_keeps_outcomes_and_drops_prose():
    from tests.golden.capture import project

    raw = {
        "ts": "2026-11-11T00:00:00",
        "outcome": "consensus",
        "why": "All three agents accepted C2.",
        "votes": {"atc": {"accept": True, "reason": "fine"}},
        "violations": ["C-FUEL-1: fuel margin -3 min < 0"],
        "scores": {"C1": [0.5, "slot 20:15"]},
        "world": {"date": "2015-04-24", "mode": "dry run (no LLM)"},
    }
    assert project(raw) == {
        "outcome": "consensus",
        "votes": {"atc": {"accept": True}},
        "violations": ["C-FUEL-1"],
        "scores": {"C1": 0.5},
        "world": {"date": "2015-04-24"},
    }
