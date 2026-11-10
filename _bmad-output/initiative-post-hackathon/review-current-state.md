# Review: state of the codebase after the hackathon (2 Nov 2026)

Lenses: adversarial and verification-gap (`bmad-review`), applied to the whole repository at `3dd2f6f`. Findings use the lens shape: **location · trigger · fix · consequence**. Unranked, as the lens requires; the build order in `tickets/tickets.toml` is where priority lives.

## Evidence

| Check | Result |
|---|---|
| Unit tests (`pytest mediator/test_core.py fallback/tests ground_agent/tests tests/test_pilot.py`) | **74 passed** in 14 s. No ATC tests. No CI. No pytest config (tests are found by path). |
| One dry-run negotiation (`python -m mediator.run`, no LLM) | Works end to end: consensus, JSONL log and decision record written. **9.2 s**, of which **8.6 s is CSV parsing**: `flights.csv` (358,774 rows) is read in full **three times** (1,076,648 rows). The negotiation logic itself takes milliseconds. |
| Python | 3.13; `requirements.txt` mixes pins (`pydantic==2.14.2`, `pytest==9.2.0`) and floors (`anthropic>=2.3`, `streamlit>=1.40`). No `pyproject.toml`; packages are importable only from the repo root plus a `sys.path` hack. |
| Size | ~6,400 lines of Python, ~2,500 lines of Markdown (excluding `.claude/skills`, which tracks 438 unrelated files). |
| Docs | Strong: README, architecture with diagrams, 3 ADRs, an honest RESULTS.md that lists 7 bugs. CLAUDE.md is stale (see F13). |

## Duplication map (the root cause: "don't edit another person's folder")

| Concern | Implementations today | Target |
|---|---|---|
| Build the world from a DOT row | `atc-agent/atc_agent/world_stub.py` (docstring: "Stub … until team B's build_world lands"), `ground_agent/inputs.py`, `agents/pilot_inputs.py`, `fallback/world.py` | one `world` module + per-agent views |
| Read `flights.csv` | `world_stub.load_day`, `pilot_inputs.load_schedule`, `ground_agent/inputs._read_rows`, `app.py`, `app_prime.py`, `evaluation/evaluate.py`, 2 test files | one cached loader |
| HHMM ↔ minutes | `world_stub`, `ground_agent/timeutil.py`, `pilot_inputs`, `fallback/solver._hhmm`, `fallback/rules.to_min`, `app.py`, `app_prime.py` | one `timeutil` |
| Hindsight columns | `atc_agent/config.HINDSIGHT_COLUMNS`, `fallback/config.HINDSIGHT_COLUMNS`, `ground_agent/agent.FORBIDDEN_FIELDS` (lower-case, smaller), plus allow-lists in pilot and ground inputs | one definition, enforced by the loader |
| Hard-rule checks | `atc_agent/menu.check_slot`, `ground_agent/checker.py`, `agents/pilot.assess_plan`, `fallback/rules.check`, `mediator/adapters.check_plan` (filters ATC's fuel result) | one rule registry |
| Cost weights | `atc_agent/config.py` ("Cost stub until team B's cost model lands"), `ground_agent/cost_config.py`, `fallback/config.py` (copies with "see other file" comments), `evaluation/evaluate.py:119` (literal `5.0`) | one cost module + one config |
| Message contract | `agents/schema.py` (Pydantic), `atc_agent/schema.py` (dict validator), `mediator/core.py` (`ScoredPlan`, `Vote`), `atc-agent/agent-spec/agent-contract/message-schema.md` (v0.2), framing §4 (`RANK/PROPOSE/…`), CLAUDE.md §7 | one contracts module, versioned |
| Claude calls | ATC: sync `Anthropic().messages.create` + `text.find("{")` JSON parsing + own disk cache + own `.env` reader; Pilot and Ground: `AsyncAnthropic().messages.parse` with Pydantic, separately | one LLM client layer |
| Run a negotiation | `middleman.negotiate`, `mediator/run.main`, `mediator/eval_batch.run_one`, `evaluation/evaluate.py` (same context dict copy-pasted) | one `negotiate()` service |
| Fallback | `fallback/scenario.py` (used everywhere) and `fallback/world.py` + `rules.py` + `solver.py` (~390 lines, used only by its own CLI and tests, though its docstring calls it "the evaluation baseline") | one fallback on the shared world |
| Evaluation | `mediator/eval_batch.py` (30 DFW rows → `results/eval_summary.json`, read by the UI) and `evaluation/evaluate.py` (32 stratified rows → `docs/RESULTS.md`) | one harness |
| UI | `app.py` (400 lines) and `app_prime.py` (513 lines), largely the same functions | one UI |

## Findings

**F1 — Four world builders disagree.**
`ground_agent/inputs.py:160` sets Ground's "now" from `sched + delay` for every event, while ATC lands weather flights near schedule (`world_stub.build_world`).
Fix: one `build_world(row, seed)` that computes the disrupted arrival once; agents receive views of it.
Consequence: false "no valid plan" (RESULTS.md §5 item 4, DFW-20150303-MQ3275), and any new field drifts four ways.

**F2 — The checker is assembled from lane fragments and overrides one of them.**
`mediator/adapters.py:71` drops ATC's `C-FUEL-1` because ATC's stub uses the wrong limit (`atc-agent/atc_agent/menu.py:93`, `extra = max(0, hold - HOLDABLE_MIN)` with 45 min).
Fix: one rule registry; each rule id has exactly one implementation.
Consequence: "depart on time and hold" is never available (468 of 580 hold options fail, RESULTS.md §5 item 2), and future rules can be silently shadowed.

**F3 — Three copies of the cost weights, and the system cost leaves out late-arrival missed connections.**
`atc_agent/config.py:44`, `ground_agent/cost_config.py`, `fallback/config.py:28-38`, `evaluation/evaluate.py:119`.
Fix: one `cost` module and one labelled config; add the Pilot's `pax_missed` term.
Consequence: a weight change in one place splits the mediator, fallback and evaluation; the system adds delay that strands passengers (RESULTS.md §5 item 1).

**F4 — Lane folders are not a package.**
`atc-agent/` has a hyphen, so `mediator/adapters.py:21` and `fallback/world.py:14-16` insert it into `sys.path`; `fallback/rules.py:12` must import `world` first "to put atc-agent on sys.path".
Fix: `pyproject.toml`, `src/<package>/`, editable install.
Consequence: import order bugs, tools (pytest, IDEs, type checkers) see different module graphs.

**F5 — The data file is parsed three times per run.**
`world_stub.load_day`, `pilot_inputs.load_schedule`, `ground_agent/inputs._read_rows`.
Fix: one loader that reads once, indexes by (date, airport) and tail, and caches to disk.
Consequence: 9.2 s per dry run; the 32-row evaluation and any larger batch scale with it.

**F6 — The negotiation is mostly code.**
`mediator/adapters.py` `LaneAgent.propose/score` never call Claude; only `vote` does, in round 3 (ADR-0003 "Negative").
Fix: Claude chooses in every round, from code-computed menus; code still decides termination and the pick.
Consequence: the product claim "agents negotiate" rests on three yes/no votes; 29 of 31 outcomes equal the least-cost solver.

**F7 — The ATC dry-run vote rule contradicts the pick rule.**
`atc-agent/atc_agent/agent.py:134` rejects any table plan more than 5 min worse than ATC's own best; the mediator picks by Nash product.
Fix: give agents the pick's reasoning in the final round, or align the tolerance with the pick rule.
Consequence: 10 of 32 rows end in no consensus by construction, so the consensus rate measures a rule mismatch.

**F8 — Three LLM integrations with different failure behaviour.**
ATC: sync client run through `asyncio.to_thread`, hand-rolled JSON extraction (`agent.py:36`), its own `.env` reader (`agent.py:22`), cache in `atc-agent/.cache`, logs in `atc-agent/logs`. Pilot and Ground: async `messages.parse`, logs elsewhere. `agents/pilot.py:22,30` imports `anthropic` and reads its prompt at import time, so dry runs still need the SDK.
Fix: one client wrapper (structured output, prompt caching, retry-once, response cache, call log with usage and latency).
Consequence: inconsistent retries and logs; live cost and latency are "not yet measured" (architecture §8).

**F9 — The human's decision is not logged.**
`app_prime.py:465-478` holds Approve/Reject in the Streamlit session only (architecture §9).
Fix: append a `human_decision` line to the run's consensus log.
Consequence: the audit trail stops one step before the decision it exists to support.

**F10 — The mediator's wording and the bridge hard-code the old protocol.**
`mediator/core.py:210` says "Hand over to the human-in-the-loop fallback" (the fallback is code); `middleman.py:83` returns `"rounds": 3 if … else 1`.
Fix: the outcome carries the actual round count and the real next step.
Consequence: misleading logs; any change to the round cap breaks the UI silently.

**F11 — Weather barely disrupts medium hubs.**
`atc-agent/atc_agent/world_stub.py:69` cuts capacity only in hours with ≥ 5 weather-delayed arrivals.
Fix: always cut the focal hour when `WEATHER_DELAY > 15`, or start the focal flight at `sched + WEATHER_DELAY`.
Consequence: 7 of 8 medium-hub weather rows show zero delay and $0 cost (RESULTS.md §5 item 3), which flatters the results.

**F12 — Implausible connection counts.**
`agents/pilot_inputs.py:128-144` gives every same-airline departure 3–25 connecting passengers with no seat cap.
Fix: cap total connections at a share of the aircraft class's seats.
Consequence: a ~50-seat regional jet reports 191+ missed connections, which drives the Nash pick's headline example.

**F13 — Repo instructions describe a different project.**
CLAUDE.md's top half is the generic "Singapore task" template (Stack TBD, Roles TBD, SG API rules); the second half is the hackathon MVP with a timeline. `.env.example` lists `DATA_GOV_SG_API_KEY`, `LTA_DATAMALL_ACCOUNT_KEY`, `ONEMAP_*`.
Fix: rewrite as the project's agent instructions (BMad `bmad-project-context` writes a verified `AGENTS.md` block); keep only `ANTHROPIC_API_KEY`.
Consequence: every new session (human or agent) starts from wrong rules, such as "skip TDD" and "don't edit another person's folder".

**F14 — Dead, stale and unrelated files.**
`app.py` (superseded by `app_prime.py`), `fallback/world.py`/`rules.py`/`solver.py`/`__main__.py` (unused by the product), `mediator/eval_batch.py` (superseded by `evaluation/`), `ui/ui_implementation_plan_mock_data.md` (pre-build plan), `atc-agent/requirements.txt` and `atc-agent/.gitignore` (lane-local), `atc-agent/docs/consensus-log-proposal.md` and `atc-agent/agent-spec/` (pre-build specs, partly contradicting the code), 19 generic skills in `.claude/skills/` (438 files: fonts, GIF tools), `pitch.pptx` and the hackathon PDF at the root.
Fix: delete or move to `docs/hackathon/` (archive), per the open questions.
Consequence: readers and agents load contradicting context; BMad's own guidance says to keep greenfield context out of reach of ordinary changes.

**F15 — Tests are scattered and the most central lane has none.**
Tests live in `mediator/`, `fallback/tests/`, `ground_agent/tests/`, `tests/`; `tests/live_pilot_eval.py` is a script, not a test; ATC has no tests; nothing checks that the five demo rows or the evaluation still produce the published numbers.
Fix: one `tests/` tree, pytest config, a golden-master test over the dry-run evaluation and demo rows, CI.
Consequence: a refactor of this size cannot be verified, and RESULTS.md can drift from the code without anyone noticing.

**F16 — Generated results are committed beside source.**
`results/*.json`, `results/evaluation/*`, `docs/RESULTS.md` are outputs of scripts; `results/eval_summary.json` (live, 26/30) and `docs/RESULTS.md` (dry, 21/32) disagree and both are shown to users.
Fix: one evaluation writes one summary; keep committed outputs only as versioned, dated snapshots or golden fixtures.
Consequence: two "official" consensus rates; the UI and README quote different numbers.

**F17 — The 38 MB data file is in git.**
`data/raw/dot2015/flights.csv`. The full BTS 2015 data (needed to replace synthetic filler traffic, constraints-audit X10) is ~565 MB.
Fix: a fetch script with a checksum, or Git LFS (open question).
Consequence: clone size grows with every data change; the real-traffic extension is blocked.

## Verification gaps (claims with no check behind them)

- "0 hard-rule violations reach the duty manager" is checked only in the evaluation script, not as a test that fails CI.
- "Agents never see hindsight columns" is enforced by three different lists; no test feeds a hindsight column through `negotiate()` and asserts it never reaches a prompt.
- "Fully reproducible in dry-run mode" (ADR-0003) is not tested: nothing runs the same row twice and compares logs.
- Live-mode behaviour (retries, refusal handling, `max_tokens`) is unit-tested for Ground (`ground_agent/tests/test_agent.py`); Pilot has a happy-path concurrency test with a fake client (`tests/test_pilot.py:147`); ATC's LLM path has none.

## What is good and should be kept

- The design: LLM-Modulo split, safety as a filter, deterministic fallback, Nash pick, per-agent private facts. The ADRs record it well.
- The mediator core (`mediator/core.py`) is small, pure and tested; it is the right shape for the target architecture.
- Honest documentation: RESULTS.md names its own bugs with causes and fixes; the bug list above reuses it.
- Provenance labelling of every synthetic input.
