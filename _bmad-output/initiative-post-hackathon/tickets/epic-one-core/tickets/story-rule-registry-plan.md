---
title: 'Rule registry'
type: 'refactor'
ticket: '5'
created: '2026-11-17'
status: 'done'
baseline_revision: '5b7648b'
route: 'full'
risk: 'medium'
review: 'quick'
review_loop_iteration: 0
built_by: 'subagent (worktree)'
deferred:
  - 'Rule-id literals still outside core/rules, each listed with its reason in tests/unit/test_rules.py:
    - agents/atc/menu.py, agents/ground/checker.py and agents/ground/icap.py: structured results and facts keyed by id;
    - evaluation/evaluate.py reads ids back out of violation strings;
    - prose in mediator/adapters.py and evaluation/report.py.
    Story 8 (agents onto the core) and story 9 (evaluation) shrink the list.'
  - 'docs/RESULTS.md still names check_plan; the next republish (story 9) picks up the updated report.py prose.'
---

## Intent

The hard rules were checked in three lanes and stitched together by `mediator/adapters.check_plan`. The adapter's "no gate in plan" reused Ground's C-GATE-1 id for a different meaning.

## Commits

| Commit | What | Golden |
|---|---|---|
| `64d89e7` (1) | `core/rules/` (registry, plus `atc`, `pilot` and `ground` owner modules): one registration per id, a fixed order, and the registry owns the message format. `check_plan` deleted; callers use `core.rules.check`. ATC's fuel stub deleted: it could never fire for menu plans, and the ATC dry policy ignores it. | unchanged |
| `3dd750b` (3) | `C-PLAN-1` (every plan names a gate; owner mediator) replaces the reused C-GATE-1. Log schema 1.1 → 1.2. Architecture §5–6 updated. | Only the schema string, on 1,065 lines. No dry-run plan lacks a gate, so no id moved. |

## Verification

- Subagent: 151 passed, 1 deselected after each commit. ruff, format and lock are clean. The default row reaches consensus. Scratch proof: equal after mapping back.
- Orchestrator, on the subagent branch: pytest gives 151 passed, 1 deselected; ruff and format are clean. Commit 1 leaves the snapshot unchanged; commit 3's snapshot equals commit 1's apart from the schema string.
