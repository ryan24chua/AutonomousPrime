---
type: epic
title: "One implementation of each concern, behind one negotiate()"
parent: initiative-post-hackathon
covers: [R2, R3, R4]
sources: []
companions: []
after: [epic-safety-net-and-hygiene]
refined: true
risk: high
---

# One implementation of each concern, behind one negotiate()

## Description

Collapse the four lanes' parallel implementations into the functional core the architecture spine describes: one data loader, one world with per-role views, one contracts module, one rule registry, one cost module with a config file, one LLM client, one `negotiate()` service, one evaluation, one UI. Behaviour is preserved: where the lanes disagree today (e.g. Ground's "now"), the unified world keeps each lane's current value and the disagreement is fixed later, visibly, in epic-known-gaps-closed.

## Outcome

Anyone extending the system changes a concern in one place, and a dry run is fast enough to iterate on (< 2 s).

## Requirements

- R1 (parent R3): CLI, UI, cache script and evaluation all call `service.negotiate()`; `middleman.py` and `mediator/run.py` no longer exist; the outcome reports the rounds actually used.
- R2 (parent R4): flights.csv is parsed at most once per process and cached on disk; a dry-run negotiation takes < 2 s on the reference container (9.2 s today).
- R3 (parent R2; AD-8): outcome columns are unreachable from agents and core; a test enforces the import boundary.
- R4 (parent R2; AD-4): one `build_world()` per run; ATC, Pilot, Ground and fallback consume views of it; a test shows each view excludes the other roles' private fields.
- R5 (parent R2): one contracts module holds Plan, AgentMessage, ScoredPlan, Vote (with flags), CheckResult and the log-line schema.
- R6 (parent R2; AD-5): each rule id is registered once, in `core/rules/`; nothing else emits rule ids.
- R7 (parent R2; AD-10): one cost function; weights in `config/cost.toml` with source labels; no weight literals elsewhere.
- R8 (parent R2; AD-7): only `infra/llm.py` imports `anthropic`; all three agents use it, with the same retry, refusal, cache and call-log behaviour.
- R9 (parent R3): one evaluation harness and one summary file; the UI shows that summary.
- R10 (parent R3): one Streamlit console inside the package, reading only `service` and the evaluation summary.

## Constraints

- Golden master unchanged by every story except story 9 (UI's displayed evaluation summary switches source; plans and costs still unchanged) — AD-11.
- Architecture spine AD-1…AD-11 bind; the dependency direction diagram is a rule.
- Dry-run behaviour of each agent's vote policy is preserved, including ATC's tolerance rule (its fix belongs to epic-negotiation-beyond-three-rounds).

## Done when

- The duplication map in review-current-state.md has one implementation per row.
- Golden master, unit tests, console smoke test and CI pass on `main`.
- A timed dry run of the default row is under 2 s.
- A live run (with a key) of one demo row completes with all three agents' calls in one call log.

## Boundaries

- Belongs to epic-known-gaps-closed: fixing the RESULTS.md bugs, logging the human decision.
- Belongs to epic-negotiation-beyond-three-rounds: NegotiationPolicy, LLM in rounds 1–2, vote/pick alignment.
- Must not change: plans, costs, outcomes and rule ids in the golden master.

## References

- parent — `_bmad-output/initiative-post-hackathon/initiative-post-hackathon.md`, Requirements R2–R4
- architecture — `_bmad-output/initiative-post-hackathon/architecture-target/architecture-target.md`, AD-4…AD-11, "Where today's code goes"
- review — `_bmad-output/initiative-post-hackathon/review-current-state.md`, duplication map, F1–F5, F8, F10, F14, F16

## Notes

- Decision: 2026-11-02 — tracer bullet is story 1 (`service.negotiate()`): every entry point goes through it first, so each later story refactors behind a stable seam.
- Decision: 2026-11-02 — the world story keeps each lane's current derived values (Ground's `now`, ATC's weather hours) to hold the golden master; unifying their meaning is epic 3's bug 4.
- Assumption: stdlib pickle cache for parsed rows unless the user allows a columnar reader.
