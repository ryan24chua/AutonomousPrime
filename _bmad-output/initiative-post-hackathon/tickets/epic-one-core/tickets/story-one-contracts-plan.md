---
title: 'One contracts module'
type: 'refactor'
ticket: '4'
created: '2026-11-17'
status: 'done'
baseline_revision: '2fb4e72'
route: 'full'
risk: 'medium'
review: 'quick'
review_loop_iteration: 0
built_by: 'subagent (worktree)'
deferred:
  - 'ATC flags (agents/atc/config.FLAGS: MINIMUM_FUEL, EMERGENCY_FUEL) differ from the shared Flag literal (no EMERGENCY_FUEL). Unifying is a message-schema change: own commit, version bump, architecture §5 (story 8 role registry, or epic-negotiation typed proposals).'
  - 'Prompts hard-code the word limits (agents/atc/prompt.py:29, agents/ground/prompts/ground.md:52-57, agents/pilot/prompts/pilot.md:35): story 7 (prompts load at call time) renders them from contracts.LIMITS.'
  - 'ATC validator applies word limits with no tolerance; validate_ranges allows +5. Kept as is; epic-negotiation decides one rule.'
  - 'core/world.py crew-report formatting and agents/pilot/agent.py duty-end text still format HH:MM inline (min_to_hhmm would wrap past 24 h): story 11 sweep.'
---

## Intent

**Problem:** The message contract and the mediator's result types were defined in three places:
- `agents/schema.py`;
- ATC's own dict validator, with its own limits;
- `mediator/core.py` dataclasses.

The word limits and the retry count were literals in each agent (design-register N7).

**Approach:**
- `core/contracts.py` is the one definition: Plan, AgentMessage, ICAPBrief, Alternative, FailedConstraint, literals, `validate_ranges`, ScoredPlan, Vote, CheckResult, plus `MessageLimits` (validated at construction) with the one `LIMITS` instance and `LOG_SCHEMA_VERSION`.
- Commit 1 is a pure move. Commit 2 is the schema change, in its own commit with a version bump and architecture §5 updated.

## Commits

| Commit | What | Golden |
|---|---|---|
| `7bc823e` (1) | `core/contracts.py`. `agents/schema.py` deleted. `agents/atc/schema.py` becomes `agents/atc/validate.py` (menu-specific checks only; limits from contracts). Retry loops read `LIMITS.max_attempts` (2 calls per turn, all three agents). `slot_to_min` moves to `core/timeutil.py`. `app_prime.hhmm` uses `min_to_hhmm`. | unchanged |
| `e9b2412` (2) | `Vote.flags` (passed through from each agent's message). Every consensus-log line carries `"schema": "consensus-log/1.1"`; round-3 votes carry `flags`. Architecture §5 documents the message, limits and log line. | Only added keys: 1,065 `schema` and 99 empty vote `flags` (proven equal otherwise). |

## Review Triage Log

- 2026-11-17, orchestrator review:
  - The diff stays inside the code map.
  - Commit 1 keeps the snapshot unchanged. In commit 2, removing the two added keys gives back the old snapshot (independent script).
  - The word-limit semantics are kept per validator (validate_ranges allows +5 words; ATC allows none).
  - The four items under `deferred` are not blocking.

## Verification

- Subagent: pytest gives 142 passed, 1 deselected after commit 1, and 143 after commit 2. ruff, format and `uv lock --check` are clean. `python -m autonomousprime run` reaches consensus.
- Orchestrator, on the subagent branch:
  - pytest at each commit gives 142 and 143 passed, 1 deselected;
  - ruff, format and lock are clean;
  - the snapshot proof is equal (`{'schema': 1065, 'flags': 99}`).
