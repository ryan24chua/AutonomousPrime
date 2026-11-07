---
title: "Golden master pins today's dry-run outputs"
type: 'chore'
ticket: '1'
created: '2026-11-07'
status: 'done'
baseline_revision: '16c4f0b'
route: 'full'
route_source: 'pinned'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing proves that a refactor leaves behaviour unchanged. The 74 unit tests check pieces, not the numbers the published results and the console show.

**Approach:** Capture every dry-run output that `docs/RESULTS.md` and the console depend on into a committed JSON snapshot. One pytest test compares against it, and `python -m tests.golden.update` rewrites it when a commit means to change behaviour.

## Boundaries & Constraints

**Always:** reuse the code paths the published numbers come from (`evaluation.evaluate.evaluate_one`, `middleman.negotiate`); strip only volatile values (timestamps, run ids, file paths, latency); leave no files behind in the repo.

**Never:** call the LLM; run `evaluation.evaluate.run()`/`main()` (they rewrite `docs/RESULTS.md` and `results/`); edit product code.

</frozen-after-approval>

## Code Map

- `tests/golden/capture.py` -- builds the snapshot: the demo row plus the 32-row stratified sample through `evaluate_one` (every method's plan, cost, metrics, ablations and the mediator log), and the five `demo_rows.DEMO_ROWS` through `middleman.negotiate(live=False)` (outcome, plan, UI log, decision record).
- `tests/golden/test_golden.py` -- compares the capture with the snapshot; prints a unified diff on failure (first 200 lines).
- `tests/golden/update.py` -- rewrites `tests/golden/snapshot.json`.
- `tests/golden/snapshot.json` -- 33 evaluation rows and 5 console rows, about 1.1 MB.

## Implementation Notes

- The plan text named the lower-level calls (`build_scenario`, `run_negotiation`, `solve_scenario`). The capture goes through `evaluate_one` and `middleman.negotiate` instead, which call those same functions. It also pins everything the results table and console show, not only the picked plan.
- Speed: while capturing, `middleman.load_day` and `ground_agent.inputs._read_rows` are swapped for in-memory copies that return identical rows in identical order. `evaluate.OUT` is pointed at a temporary directory. All three are restored afterwards. A full capture takes about 10 s, against roughly 9 s per uncached negotiation.
- `middleman.negotiate` writes `logs/mediator-<id>-<run_id>.jsonl`. The capture deletes each one after reading it.
- The decision record embeds the run id and the log path. Both are replaced with `<run_id>` and `<log_path>`.
- Today's console outcomes: AA36 and AA96 reach consensus in round 3; OO6213 halts with the least-cost plan; AA1480 and AA98 get "recommend cancellation" (no valid plan in dry mode). These are recorded as they are, not judged.

## Review Triage Log

- 2026-11-07, self-review by the orchestrator. The first draft left its monkeypatches in place after `capture()` returned, which would leak into later tests in the same pytest run. Fixed with a restoring context manager (`_patched`). No other findings.

## Verification

**Commands:**
- `pytest tests/golden` -- expected: passes twice in a row, and under `PYTHONHASHSEED=1` and `PYTHONHASHSEED=98765`. Done: 1 passed each time, about 10 s.
- Set `ground_agent/cost_config.GROUND_DELAY_PER_MIN` to 50.0, then run `pytest tests/golden` -- expected: fails with a readable diff. Done: 5,116 diff lines, starting `"cost": 12766.5` → `12915.5`. Reverted afterwards.
- `pytest tests/golden tests/test_pilot.py mediator/test_core.py fallback/tests ground_agent/tests` -- expected: all pass. Done: 75 passed.
- `git status --short` -- expected: only `tests/golden/` is new; no new files under `logs/`, and `docs/RESULTS.md` and `results/` are unchanged. Done.
