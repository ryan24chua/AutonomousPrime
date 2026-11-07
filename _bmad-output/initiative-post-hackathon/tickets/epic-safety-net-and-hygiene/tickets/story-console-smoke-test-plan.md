---
title: 'Console smoke test'
type: 'chore'
ticket: '3'
created: '2026-11-07'
status: 'in-progress'
baseline_revision: 'acfa4c6'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** No test opens the Streamlit console (`app_prime.py`), the only UI the duty manager uses. A refactor can break it silently.

**Approach:** Add a headless `streamlit.testing.v1.AppTest` test that drives the console in replay mode through every demo row. For each row it presses "Find a recovery plan", checks the recommendation and the two decision buttons, and records a decision.

## Boundaries & Constraints

**Always:**
- Replay mode only. The "Replay saved run" toggle is on by default and reads `results/<row_id>.json`, so no API key is needed.
- The test runs in CI without a key and writes no files.

**Never:**
- Edit `app_prime.py`. The one exception: adding a `key=` to a widget if AppTest cannot otherwise address it stably. Say so in the report.
- Turn off replay.
- Patch the app's internals.
- Change `results/`.
- Add dependencies.
- Push.

</frozen-after-approval>

## Code Map

- `app_prime.py:381` -- `st.selectbox("Disrupted flight", list(DEMO_ROWS), ...)` in the sidebar, with no key.
- `app_prime.py:382` -- the `st.toggle("Replay saved run", value=True)`.
- `app_prime.py:422` -- `st.button("Find a recovery plan")`. In replay mode it sleeps 1 s twice, then loads `results/<row_id>.json`.
- `app_prime.py:449` -- `st.subheader("Recommended plan")`.
- `app_prime.py:465-471` -- the decision buttons, keyed by label. With a plan they are "Approve plan" / "Reject plan". With no plan they are "Confirm cancellation" / "Override: keep flying". Clicking one sets `st.session_state["approval"]["decision"]`, to "Approved" / "Rejected" / "Cancellation confirmed" / "Overridden".
- `demo_rows.DEMO_ROWS` -- the five row ids. Cached outcomes:
  - With a plan: AA36_SAN_DFW_weather (consensus), AA96_STL_DFW_late (consensus), OO6213_CVG_ORD_weather (halt_least_cost).
  - No plan (recommend_cancel): AA1480_MCI_DFW_weather, AA98_MSY_DFW_late.
- New `tests/unit/ui/__init__.py` and `tests/unit/ui/test_console.py`.

## Tasks & Acceptance

**Execution:**
- `tests/unit/ui/test_console.py`:
  - Locate `app_prime.py` from the repo root, derived from the test file's path.
  - Build `AppTest.from_file(..., default_timeout=180)`. The first run reads the 37 MB flights CSV.
  - Parametrize over `DEMO_ROWS`. For each row:
    1. Run the app, select the row, and assert the replay toggle is on.
    2. Click "Find a recovery plan" and run.
    3. Assert no `at.exception` and no `at.error`.
    4. Assert a "Recommended plan" subheader.
    5. Assert the expected pair of decision buttons, derived from whether `results/<row_id>.json` has a `final_plan`.
    6. Click the first decision button and assert the recorded decision.
- Commit as `story 1.3: Console smoke test`.

**Acceptance Criteria:**
- Given no `ANTHROPIC_API_KEY`, when `pytest tests/unit/ui` runs, then 5 tests pass and nothing in the repo changes.
- When `pytest` runs, then all earlier tests still pass and the golden master is unchanged.

## Implementation Notes

## Review Triage Log

## Verification

**Commands** (run with `env -u ANTHROPIC_API_KEY`):
- `pytest -q tests/unit/ui` -- expected: 5 passed. Report the wall time; if it is over 120 s, report that rather than optimising.
- `pytest -q` -- expected: all pass, with 5 more than before
- `ruff check . && ruff format --check .` -- expected: exit 0
- `git status --short` -- expected: clean after commit
