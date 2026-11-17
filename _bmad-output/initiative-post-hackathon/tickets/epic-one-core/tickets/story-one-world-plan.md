---
title: 'One world with per-role views'
type: 'refactor'
ticket: '3'
created: '2026-11-17'
status: 'done'
baseline_revision: '6ee9c10'
route: 'full'
risk: 'high'
review: 'self (orchestrator-built)'
review_loop_iteration: 0
built_by: 'orchestrator'
deferred:
  - 'core/world.py still imports configuration from agents/ (atc config, agents.constraints, ground assumptions) and infra.data.airports(): story 8 import-boundary test must invert these (inject limits and airports, or move the config into core/config).'
  - 'ECP, PBG, UST have no coordinates in airports.csv, so the Pilot alternate cannot be computed and build_world raises: a data gap for epic-known-gaps-closed or epic-full-2015-data.'
  - 'Hindsight lists: WorldState.focal uses ATC HINDSIGHT_COLUMNS (16 columns incl. AIR_SYSTEM_DELAY, SECURITY_DELAY, AIRLINE_DELAY); agents/atc/config.py and fallback/config.py keep their own lists. Point them at infra.data.OUTCOME_COLUMNS plus one named list of non-given delay causes (story 5 or 11).'
  - 'fallback/config.py "Synthetic world" constants (CONNECTING_PAX_RANGE, CONNECTION_SLACK_RANGE, CREW_END_SLACK_RANGE, NEXT_GATE_OCCUPANT_AFTER) look unused since the fallback runs on the mediator scenario: story 6 (cost/config) confirms and deletes.'
  - 'evaluation/report.py prose cites agents/pilot_inputs.py and world_stub.py and "scheduled gate A12": story 9 (C3, numbers only).'
  - 'The ATC menu horizon is too short for long weather events (RESULTS §5.4, second half): epic-plans-time-and-events.'
---

## Intent

**Problem:** Three lane builders (ATC `world_stub`, Pilot `inputs`, Ground `inputs.build_world`) plus the console's own build each derived the world from the same row and disagreed on several things:
- the disrupted arrival and Ground's "now";
- the event type;
- the year filter;
- "2400";
- the seeding.

The synthetic gate world crashed at 30-gate-or-smaller airports, fixed every scheduled gate at A12, and shared one RNG across flights (design-register P2, W1, W3; RESULTS §5.4).

**Approach:** First commit A, a pure move to `core/world.py`, with the golden master unchanged. Then one commit per unification or fix, each regenerating the snapshot and stating the numbers that moved.

## Commits

| Commit | What | Golden numbers |
|---|---|---|
| `c63cb52` A | Adds `core/world.py`:<br>• `WorldState` (frozen), with views `World` (ATC), `PilotInputs` and `GroundState` (renamed from ground's `WorldState`);<br>• `build_world`, built once per negotiate.<br>Adds `core/timeutil.py` (ground timeutil deleted) and `infra.data.airports()`.<br>Deletes `world_stub.py` and `pilot/inputs.py`. `ground/inputs.py` keeps `walk_min` only. `service.build_world_for` serves the console, demos and tests. | unchanged |
| `6fbbdd7` B1 | One earliest arrival (`earliest_arrival_min`; late aircraft only pushes it). Ground's disrupted arrival and "now" follow it. `GroundState.event_end_min` (sched + reported delay, S5) anchors the synthetic draws and the unavoidable knock-on. | 8 weather rows:<br>• MQ3275 no_valid_plan → consensus;<br>• AA1131 and OO6213 no_consensus → consensus;<br>• demo full cost $50,115 → $49,561. |
| `56efb56` B2 | One `event_of` for all views (the Pilot's `w >= late` rule is gone; 6,373 file rows affected). | none (the Pilot's event type is prompt-only) |
| `1e30f45` B3 | One date per world (`date_of`, ValueError otherwise); the evaluation keys days by (YEAR, MONTH, DAY). | none |
| `17b9bc1` B4 | "2400" = 1440 (end of the scheduled day) everywhere; the Pilot shows "24:00". | none |
| `b01728e` B5 | `flight_rng`: seed + full date + flight + origin + view. | All rows. Sample consensus 24 → 19; the mean negotiated cost $822 → $1,759; the shared spare gate B20 is gone. |
| `cd5e510` B6 | Gates for any airport size (spares from another terminal, or another gate). 317 of 320 destinations build; SJC (Small hub) and PNS (8-gate Non-hub) negotiate end to end. | none |
| `c801cfa` B7 | The scheduled gate is a per-flight draw (own stream); the unused `SCHEDULED_GATE = "A12"` is deleted. | Gate labels; mean cost moves by $4; consensus unchanged. |

## Verification

- Ticket verify line:
  - Pure-move commit A left the golden master unchanged. Each unification commit states its moved numbers.
  - DFW-20150303-MQ3275 now reaches consensus (09:11, B5).
  - `build_world` succeeds for a Small-hub and a Non-hub row (`test_gate_world_works_at_any_airport_size`).
  - `test_view_excludes_other_roles_private_fields` shows each role view excludes the other roles' private fields.
  - `test_build_world_runs_once_per_negotiate` shows `build_world` is called once per negotiate.
- Also tested:
  - frozen state;
  - a hindsight-free focal;
  - one shared arrival and one event classifier;
  - date guard;
  - "2400";
  - per-flight draws and scheduled gate.
- Full `pytest`: 115 passed, 1 deselected. `ruff check` and `ruff format --check` are clean.
- RESULTS.md was not republished: story 9 republishes it, and its changed numbers must match the B1, B5 and B7 statements above.
