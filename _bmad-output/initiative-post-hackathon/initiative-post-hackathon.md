---
type: initiative
title: "AutonomousPrime has one clean, tested core and negotiates beyond the hackathon's limits"
sources:
  - docs/hackathon/challenge-2-brief.md
  - docs/hackathon/challenge-2-framing.md
  - docs/architecture.md
  - docs/RESULTS.md
  - docs/adr/0001-nash-product-pick.md
  - docs/adr/0002-safety-as-filter-not-cost.md
  - docs/adr/0003-code-mediator-fixed-three-rounds.md
  - docs/hackathon/mvp-spec.md
  - docs/adr/0004-post-hackathon-design-baseline.md
companions:
  - _bmad-output/initiative-post-hackathon/design-register.md
  - _bmad-output/initiative-post-hackathon/constraints-audit.md
  - _bmad-output/initiative-post-hackathon/review-current-state.md
  - _bmad-output/initiative-post-hackathon/architecture-target/architecture-target.md
after: []
risk: medium
---

# AutonomousPrime has one clean, tested core and negotiates beyond the hackathon's limits

## Description

The hackathon build works end to end and is honestly documented, but it carries the contest's shape: a fixed three-round protocol in which Claude only votes, four lanes that each rebuilt the world, rules, costs and LLM calls because nobody could edit another lane's folder, and demo-first scaffolding. This initiative first refactors the repo into one installable package with one implementation of each concern, behind a golden-master test so behaviour is preserved; then fixes the known bugs one at a time with measured before/after numbers; then retires the constraints that only existed for judging (design-register.md, which supersedes constraints-audit.md) so the agents negotiate for real, airborne flights and diversion are supported, and the evaluation is large enough to trust.

## Outcome

For the OCC duty manager (and the team extending the system), a recovery plan comes from a negotiation between delegates of the organisations involved (traffic management, the airline, the airport and ground handler). In it every agent acts in every round under a bounded, configurable protocol, on one consistent world model built from the full 2015 data. The plan covers every flight a disruption hits, with its cascading effects predicted, and the decision is logged. It is measured on ≥ 200 real disruptions against the same baselines as today (RESULTS.md headline table).

## Requirements

- R1 (memlog; RESULTS.md headline): one command reproduces today's outputs (dry-run negotiation, 32-row evaluation, 5 demo rows), and a test fails when any of them change without an accepted golden-master update.
- R2 (review F1–F5, F8; mvp-spec "Roles"): the codebase is one installable package with exactly one implementation each of: world building, data loading, time helpers, hindsight filtering, hard rules, cost, message contracts and LLM access.
- R3 (review F14, F16): one `negotiate()` entry point serves the CLI, the UI and the evaluation; one UI; one evaluation harness; one published results summary.
- R4 (review F5): a dry-run negotiation completes in under 2 s on the reference container (9.2 s today).
- R5 (constraints-audit X1, X6; ADR-0003 follow-ups): the negotiation round cap, wall-clock and LLM-call budgets are configuration; every agent's LLM acts in every round, proposing or choosing among code-computed options, with code validating every proposal and recomputing every number; termination, pick and fallback stay in code.
- R6 (RESULTS.md §5 items 1–4, 6): each of these five bugs is fixed, with its before/after number in RESULTS.md, or parked with a reason.
- R7 (constraints-audit L3, L4; ADR-0002 gaps): airborne scenarios work end to end — holding limited by fuel on board, diversion to the alternate as an option the mediator and the fallback can choose; cancellation stays a recommendation.
- R8 (review F9; architecture §9): the duty manager's approve/reject is appended to the run's consensus log with timestamp and plan id.
- R9 (constraints-audit X12; framing §7): the evaluation covers ≥ 200 rows over ≥ 3 world seeds, reports live-LLM cost, latency and tokens per run, and shows at least one failure with its cause.
- R10 (review F13): the repo's agent instructions describe the project as it is now; no hackathon template, SG API keys, TBD sections or folder-ownership rule remain.
- R11 (design-register S1, S4, N10–N13): one disruption that hits several flights is recovered in one negotiation. Each agent is its organisation's delegate and decides its own domain, and they negotiate where domains meet. Agents make typed proposals that code validates. Without agreement, the duty manager chooses between the two best checked plans, with the fallback computed.
- R12 (design-register S4, S5): a plan's cascading effects along tail rotations, crew duty and passenger connections for the rest of the day are predicted and costed in code from the delays already known at decision time. Evaluation alone compares them with the 2015 record.
- R13 (design-register S2): the full 2015 DOT data (all flights, ~5.8 M rows) is fetched by a checksummed script, kept out of git and read through the one loader; real flights replace synthetic background traffic.

## Constraints

The product invariants (AGENTS.md; ADR-0004):
- Code computes every number, checks every rule and decides termination and the pick. The LLM proposes, chooses and explains; code validates its proposals.
- Every negotiation is bounded and terminates in code; a deterministic fallback always exists.
- Safety rules filter plans and are never priced; a final check runs before any plan leaves the mediator (ADR-0002).
- Agents never see outcome columns (mvp-spec §6).
- A human approves or rejects every outcome; cancellation is never applied automatically.
- Every step is logged; every synthetic input is seeded and labelled with its provenance (mvp-spec §6).

Rules for the work:
- Refactor commits (R1–R4) keep the golden master's plans, costs and outcomes. A change to any of them, including a bug fix inside a refactor epic, is its own reviewed commit that states which numbers moved (memlog decision; ADR-0004).
- The current design defaults (three roles in separate calls, code-built menus, fallback after three rounds, one LLM gateway on the Anthropic SDK, Streamlit) change only through an ADR (ADR-0004; design-register G1–G4).

## Done when

- `pytest` runs in CI on every push, including the golden-master test, and passes on `main`.
- The repo has one package, one UI, one evaluation, one `negotiate()`; the duplication map in review-current-state.md has no row with more than one implementation.
- A live run on any evaluation row shows Claude acting in every round, and the published RESULTS.md reports consensus rate, cost vs status quo and vs least-cost solver, leaked violations (0), and per-run LLM cost and latency on ≥ 200 rows.
- An airborne scenario that exhausts its holding fuel produces a diversion plan that passes the checker and reaches the duty manager.
- The UI's approve/reject appears in the consensus log of that run.

## Boundaries

Nothing below is ruled out. Each item is "Not yet", with the trigger that brings it in (design-register P4).
- Not yet: live operational feeds, real gate layouts, FAA Part 117 crew legality, RECAT/CWT wake categories, aircraft registry enrichment. Trigger: a data source for it. Each lands as a world field with provenance and, if it is a rule, a new rule id.
- Not yet: another front end or an API, an agent framework or another LLM provider, a database beyond JSONL logs. Trigger: a user or a need the current stack cannot meet; each needs an ADR (architecture spine "Deferred").
- In (decision 2026-11-11, design-register S4): several flights recovered at once (epic-several-flights-at-once), staged so the duty manager's airline brings all its affected flights first and other airlines get their own agents next.
- Not yet: other years and non-US data. Trigger: a question the 2015 US data cannot answer.
- Must not change: the product invariants (AGENTS.md, ADR-0004). The meaning of an existing rule id (C-CAP-1, C-FUEL-1, C-CREW-1/2, C-GATE-1/2, C-TURN-1) never changes; a changed meaning gets a new id.
- Tracer path: DOT row → one world → three agents → mediator → checker/cost → fallback → decision record → UI approve → log line.

## References

- register — `_bmad-output/initiative-post-hackathon/design-register.md` (every design choice that limits the project, with its ruling; supersedes the constraints audit)
- constraints — `_bmad-output/initiative-post-hackathon/constraints-audit.md` (history: the first Retire / Relax / Keep pass)
- review — `_bmad-output/initiative-post-hackathon/review-current-state.md` (findings F1–F17, duplication map, verification gaps)
- architecture — `_bmad-output/initiative-post-hackathon/architecture-target/architecture-target.md` (AD-1…AD-10, target layout)
- results — `docs/RESULTS.md` §5 (bug list feeding R6)
- adr — `docs/adr/0001…0003` (follow-ups feeding R5, R7)

## Notes

- Scope (decided 2026-11-11): the airline OCC duty manager at a US hub is the user; agents are delegates of their organisations; several flights at once with cascading effects; the full 2015 DOT data. Today's code still handles one delayed arrival on the organisers' delayed-only subset.
- Assumption: Python 3.13; package `autonomousprime` under `src/`. Streamlit is the current UI, a default rather than an assumption (design-register P5).
- Assumption: GitHub Actions is acceptable for CI.
- Decision: 2026-11-02 — the hackathon is over; contest-only constraints are retired per constraints-audit.md (user direction, this session).
- Decision: 2026-11-02 — refactor before features, behind a golden master; bug fixes that move numbers come after, one per commit.
- Decision: 2026-11-02 — split into six epics by outcome (see `tickets/tickets.toml`); the first two are the refactor and are sliced into stories now; epics 3–6 stay thin until refined.
- Decision: 2026-11-02 — architecture spine `architecture-target/` adopted as a companion; epics cite its AD ids.
- Decision: 2026-11-03 — user: dev-only ruff and a GitHub Actions CI are allowed; `pitch.pptx`, the hackathon PDFs and the ATC specs move to `docs/hackathon/`; `.claude/skills/` stays as is; BMad skills stay local.
- Decision: 2026-11-10 — user: no columnar reader for now. The data cache uses the standard library, one cache file per date (epic-one-core story 2). Revisit duckdb when the full BTS data or epic-evaluation-at-scale starts.
- Decision: 2026-11-11 — user approved the design-choice register (`design-register.md`, 45 rows) with its recommended rulings. Only rules with a product reason stay invariants (ADR-0004); brief-only rules become defaults changed by ADR; the golden master pins plans, costs, outcomes, rule ids and round counts, and bug fixes may land inside refactor epics as their own commits; "Out" lists become "Not yet" with triggers. Open: S1, S2, S4, S5, G8, P6, K1.
- Decision: 2026-11-11 — user, register second pass. The OCC duty manager stays the user, and the agents are delegates of their organisations (S1). The full 2015 DOT file is fetched by a checksummed script and kept out of git, which also answers the `flights.csv` storage question (S2). Several flights at once and cascading effects are in scope (S4). The recorded delay is the given disruption, labelled "known at decision time" (S5). The AGENTS.md bmad markers are removed (G8). A lockfile is added and run logs stay per-run JSONL (K1).
- Decision: 2026-11-11 — user: build order after epic 1 is 2 → 3 → 7 → 8 → 10 → 4 → 9 → 5 → 6 (one core, known gaps, plans/time/events, full data, cascades, negotiation, several flights, airborne, evaluation at scale): honest numbers first, then the protocol, then many parties (P6). New epics 8, 9, 10.
- Decision: 2026-11-11 — user, for epic-negotiation (register N10–N13). The authority model: each organisation decides its own domain, and they negotiate where domains meet. Typed proposals are validated by code. Organisations share need, offer, interests, red lines, concessions and flags, and keep raw data private. Without agreement the duty manager chooses between the two best checked plans, with the fallback still computed.
