---
type: initiative
title: "AutonomousPrime has one clean, tested core and negotiates beyond the hackathon's limits"
sources:
  - docs/challenge-2-brief.md
  - docs/challenge-2-framing.md
  - docs/architecture.md
  - docs/RESULTS.md
  - docs/adr/0001-nash-product-pick.md
  - docs/adr/0002-safety-as-filter-not-cost.md
  - docs/adr/0003-code-mediator-fixed-three-rounds.md
  - CLAUDE.md
companions:
  - _bmad-output/initiative-post-hackathon/constraints-audit.md
  - _bmad-output/initiative-post-hackathon/review-current-state.md
  - _bmad-output/initiative-post-hackathon/architecture-target/architecture-target.md
after: []
risk: medium
---

# AutonomousPrime has one clean, tested core and negotiates beyond the hackathon's limits

## Description

The hackathon build works end to end and is honestly documented, but it carries the contest's shape: a fixed three-round protocol in which Claude only votes, four lanes that each rebuilt the world, rules, costs and LLM calls because nobody could edit another lane's folder, and demo-first scaffolding. This initiative first refactors the repo into one installable package with one implementation of each concern, behind a golden-master test so behaviour is preserved; then fixes the known bugs one at a time with measured before/after numbers; then retires the constraints that only existed for judging (constraints-audit.md) so the agents negotiate for real, airborne flights and diversion are supported, and the evaluation is large enough to trust.

## Outcome

For the OCC duty manager (and the team extending the system), a recovery plan comes from a negotiation in which every agent acts in every round under a bounded, configurable protocol, on one consistent world model, with the decision logged, measured on ≥ 200 real disruptions against the same baselines as today (RESULTS.md headline table).

## Requirements

- R1 (memlog; RESULTS.md headline): one command reproduces today's outputs (dry-run negotiation, 32-row evaluation, 5 demo rows), and a test fails when any of them change without an accepted golden-master update.
- R2 (review F1–F5, F8; CLAUDE.md "Roles"): the codebase is one installable package with exactly one implementation each of: world building, data loading, time helpers, hindsight filtering, hard rules, cost, message contracts and LLM access.
- R3 (review F14, F16): one `negotiate()` entry point serves the CLI, the UI and the evaluation; one UI; one evaluation harness; one published results summary.
- R4 (review F5): a dry-run negotiation completes in under 2 s on the reference container (9.2 s today).
- R5 (constraints-audit X1, X6; ADR-0003 follow-ups): the negotiation round cap, wall-clock and LLM-call budgets are configuration; every agent's LLM acts in every round, choosing only among code-computed options; termination, pick and fallback stay in code.
- R6 (RESULTS.md §5 items 1–4, 6): each of these five bugs is fixed, with its before/after number in RESULTS.md, or parked with a reason.
- R7 (constraints-audit L3, L4; ADR-0002 gaps): airborne scenarios work end to end — holding limited by fuel on board, diversion to the alternate as an option the mediator and the fallback can choose; cancellation stays a recommendation.
- R8 (review F9; architecture §9): the duty manager's approve/reject is appended to the run's consensus log with timestamp and plan id.
- R9 (constraints-audit X12; framing §7): the evaluation covers ≥ 200 rows over ≥ 3 world seeds, reports live-LLM cost, latency and tokens per run, and shows at least one failure with its cause.
- R10 (review F13): the repo's agent instructions describe the project as it is now; no hackathon template, SG API keys, TBD sections or folder-ownership rule remain.

## Constraints

- LLM-Modulo split: code computes every number, checks every rule, decides termination and the pick; the LLM proposes, chooses among code options and explains (brief "what to avoid"; framing §2).
- The three roles are never merged into one prompt; each agent sees only its own facts (brief).
- Negotiation always terminates in code; any non-consensus ends in the deterministic non-AI fallback (brief; ADR-0003 intent).
- Safety rules filter plans and are never priced; a final check runs before any plan leaves the mediator (ADR-0002).
- Agents never see outcome columns (CLAUDE.md §6).
- A human approves or rejects every outcome; cancellation is never applied automatically (brief; CLAUDE.md §4).
- Every synthetic input is seeded and labelled with its provenance (CLAUDE.md §6).
- The refactor (R1–R4) preserves behaviour: any change to a golden-master number is a separate, reviewed commit (memlog decision).
- No agent frameworks; the `anthropic` SDK plus our own loop (CLAUDE.md §15).

## Done when

- `pytest` runs in CI on every push, including the golden-master test, and passes on `main`.
- The repo has one package, one UI, one evaluation, one `negotiate()`; the duplication map in review-current-state.md has no row with more than one implementation.
- A live run on any evaluation row shows Claude acting in every round, and the published RESULTS.md reports consensus rate, cost vs status quo and vs least-cost solver, leaked violations (0), and per-run LLM cost and latency on ≥ 200 rows.
- An airborne scenario that exhausts its holding fuel produces a diversion plan that passes the checker and reaches the duty manager.
- The UI's approve/reject appears in the consensus log of that run.

## Boundaries

- Out: live operational feeds, real gate layouts, FAA Part 117 crew legality, RECAT/CWT wake categories, aircraft registry enrichment (framing §1 "Out of scope"; still out).
- Out: replacing Streamlit, adding an agent framework, or a database beyond JSONL logs (architecture spine "Deferred").
- Out for now: multi-flight negotiation (several Pilot agents) — open question below; becomes its own initiative if chosen.
- Must not change: the Keep invariants in constraints-audit.md; the meaning of existing rule ids (C-CAP-1, C-FUEL-1, C-CREW-1/2, C-GATE-1/2, C-TURN-1).
- Tracer path: DOT row → one world → three agents → mediator → checker/cost → fallback → decision record → UI approve → log line.

## References

- constraints — `_bmad-output/initiative-post-hackathon/constraints-audit.md` (Retire / Relax / Keep for every hackathon constraint)
- review — `_bmad-output/initiative-post-hackathon/review-current-state.md` (findings F1–F17, duplication map, verification gaps)
- architecture — `_bmad-output/initiative-post-hackathon/architecture-target/architecture-target.md` (AD-1…AD-10, target layout)
- results — `docs/RESULTS.md` §5 (bug list feeding R6)
- adr — `docs/adr/0001…0003` (follow-ups feeding R5, R7)

## Notes

- Assumption: the user stays the airline OCC duty manager at a US hub; data stays DOT/BTS US flights.
- Assumption: Streamlit stays the UI; Python 3.13; package `autonomousprime` under `src/`.
- Assumption: GitHub Actions is acceptable for CI.
- Assumption: extension order after the refactor is real negotiation, then realism (airborne, bug fixes), then trust and scale; epic order in `tickets/tickets.toml` follows it.
- Open question: which extension matters most to you — real negotiation, airborne/diversion realism, multi-flight negotiation, or scale/evaluation? (Epic order waits on this; the two refactor epics do not.)
- Open question: may the opening epic add dev dependencies (ruff; a columnar reader such as pyarrow or duckdb), or should the data cache use the stdlib only?
- Open question: `flights.csv` (38 MB) in git, Git LFS, or a checksummed fetch script? Full BTS 2015 data (~565 MB) for real background traffic cannot live in git.
- Open question: keep the 19 generic Anthropic skills in `.claude/skills/` (438 files)? Commit the BMad skills for the team, or keep them local as `.gitignore` says today?
- Open question: keep `pitch.pptx` and the hackathon PDF in the repo, move them to `docs/hackathon/`, or attach them to a GitHub release?
- Open question: is multi-flight negotiation in scope for this initiative?
- Decision: 2026-11-02 — the hackathon is over; contest-only constraints are retired per constraints-audit.md (user direction, this session).
- Decision: 2026-11-02 — refactor before features, behind a golden master; bug fixes that move numbers come after, one per commit.
- Decision: 2026-11-02 — split into six epics by outcome (see `tickets/tickets.toml`); the first two are the refactor and are sliced into stories now; epics 3–6 stay thin until refined.
- Decision: 2026-11-02 — architecture spine `architecture-target/` adopted as a companion; epics cite its AD ids.
