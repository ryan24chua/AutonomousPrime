"""Console smoke test: drive app_prime.py headless in replay mode through every demo row.

No API key needed and no files written: replay reads results/<row_id>.json.
"""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from demo_rows import DEMO_ROWS

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "app_prime.py"

PLAN_BUTTONS = (("Approve plan", "Approved"), ("Reject plan", "Rejected"))
CANCEL_BUTTONS = (("Confirm cancellation", "Cancellation confirmed"), ("Override: keep flying", "Overridden"))


@pytest.mark.parametrize("row_id", list(DEMO_ROWS))
def test_console_replay_row(row_id):
    saved = json.loads((ROOT / "results" / f"{row_id}.json").read_text())
    expected = PLAN_BUTTONS if saved.get("final_plan") else CANCEL_BUTTONS

    # First run reads the 37 MB flights CSV.
    at = AppTest.from_file(str(APP), default_timeout=180).run()
    assert not at.exception

    at.selectbox[0].select(row_id).run()
    assert at.selectbox[0].value == row_id
    assert at.toggle[0].label == "Replay saved run"
    assert at.toggle[0].value is True

    [find] = [b for b in at.button if b.label == "Find a recovery plan"]
    find.click().run()
    assert not at.exception
    assert not at.error
    assert "Recommended plan" in [s.value for s in at.subheader]

    labels = [b.label for b in at.button]
    for label, _ in expected:
        assert label in labels
    for label, _ in {*PLAN_BUTTONS, *CANCEL_BUTTONS} - set(expected):
        assert label not in labels

    first_label, first_decision = expected[0]
    [btn] = [b for b in at.button if b.label == first_label]
    btn.click().run()
    assert not at.exception
    assert at.session_state["approval"]["decision"] == first_decision
