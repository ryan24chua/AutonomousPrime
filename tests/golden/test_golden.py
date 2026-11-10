"""Golden master: today's dry-run outputs must not change unless a commit means them to.

If this fails after a pure refactor, the refactor changed behaviour: fix the code, not the snapshot.
If the change is intended, run `python -m tests.golden.update` and say in the commit which numbers moved.
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
