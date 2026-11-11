---
title: 'Golden master pins outcomes, not prose'
type: 'chore'
ticket: '12'
created: '2026-11-11'
status: 'done'
baseline_revision: '8ab5ce9'
route: 'full'
risk: 'low'
review: 'quick'
review_loop_iteration: 0
deferred: []
---

## Intent

**Problem:** The golden master compares 1.09 MB of output byte for byte, reason text and decision-record markdown included. Every wording change fails it, so it freezes prose and known bugs instead of guarding behaviour (design-register P1, ADR-0004).

**Approach:** `tests/golden/capture.py` projects each captured run onto what matters: plans, plan ids, costs, metrics, scores, vote booleans, check results with rule ids, outcomes and round counts. Regenerate the snapshot once, with no pinned value changing.

**Always:** a pure projection; no product code changes.
**Never:** call the LLM; run `evaluation.evaluate` main/run; change any pinned value.

## Code Map

- `tests/golden/capture.py`: `project()` drops `PROSE_KEYS` (`reason`, `why`, `neg_why`, `r1_reasons`, `r2_reasons`, `need`, `offer`, `consensus_rule`, `pick_rule`, `document`) and the console header labels (`world.data`, `world.mode`, `world.synthetic_inputs`). It reduces `violations` / `pick_violations` to rule ids and round-2 `scores` from `[score, reason]` to the score. It replaces `_strip` (volatile keys are still dropped). The decision-record rewriting is gone, because the document is no longer pinned.
- `tests/golden/test_golden.py`: docstring, plus a unit test of `project()`.
- `tests/golden/snapshot.json`: regenerated (1.09 MB → 0.86 MB).
- `AGENTS.md` "Running and verifying": what the golden master pins.

## Verification

- A scratch script (`project(old snapshot) == new snapshot`): True. Numeric leaves are 14,002 old and 14,002 new; the only strings with spaces left are flight labels and "no plan".
- A reason edit in `mediator/adapters.py` ("Passes Ground hard rules.", the ATC slot reason): `pytest tests/golden` passes. Reverted.
- `GROUND_DELAY_PER_MIN` 49 → 50 in `agents/ground/cost_config.py`: fails with 2,953 diff lines, starting `"cost": 12766.5` → `12915.5`. Reverted.
- Full `pytest`: 76 passed, 1 deselected. `ruff check` and `ruff format --check` are clean. `pytest tests/golden` under `PYTHONHASHSEED=98765` passes.
