---
type: epic
title: "Behaviour is pinned by tests and CI; the repo holds only the product"
parent: initiative-post-hackathon
covers: [R1, R10]
sources: []
companions: []
after: []
refined: true
risk: low
---

# Behaviour is pinned by tests and CI; the repo holds only the product

## Description

Before anything moves, pin what the system does today so the refactor can prove it changed nothing. Then make the repo a normal Python project (one package, one test tree, CI) and remove what only existed for the hackathon: the second UI, the unused standalone fallback, lane-local files, the Singapore template, and greenfield specs that contradict the code.

## Outcome

The team and coding agents work from a repo where `pytest` in CI fails on any unintended behaviour change and the instructions describe the real project.

## Requirements

- R1 (parent R1): `pytest` includes a golden-master test over the dry-run outputs of the 32-row evaluation sample, the five demo rows and the default MQ3086 run; it passes on unchanged code and fails when a cost weight or rule limit is edited.
- R2 (parent R1): CI runs lint and all tests on every push and pull request.
- R3 (parent R2, structure only): the code installs as one package (`pip install -e .`) with no `sys.path` manipulation; the golden master is unchanged by the move.
- R4 (parent R10): CLAUDE.md, AGENTS.md, README and `.env.example` describe the project as built; no hackathon template, TBD sections, SG keys or folder-ownership rule.
- R5 (review F14): files the product does not use are deleted or archived under `docs/hackathon/`.

## Constraints

- Behaviour-preserving: no golden-master number may change in this epic (architecture AD-11).
- No new runtime dependencies; dev dependencies only as agreed (initiative open question).

## Done when

- CI is green on `main` with the golden-master test included.
- `pip install -e . && pytest` works from a fresh clone with no other setup.
- `grep -rn "sys.path.insert" src/` returns nothing.
- `python -m autonomousprime.mediator.run` and the Streamlit console both work on the five demo rows (the `python -m autonomousprime run` CLI arrives in epic-one-core story 2.1).

## Boundaries

- Belongs to epic-one-core: merging duplicated logic (worlds, rules, cost, LLM clients). This epic only moves files and deletes unused ones.
- Must not change: any plan, cost, outcome or log line produced by a dry run.

## References

- parent — `_bmad-output/initiative-post-hackathon/initiative-post-hackathon.md`, Requirements R1, R10
- architecture — `_bmad-output/initiative-post-hackathon/architecture-target/architecture-target.md`, AD-11, Structural Seed
- review — `_bmad-output/initiative-post-hackathon/review-current-state.md`, F4, F13, F14, F15

## Notes

- Decision: 2026-11-02 — tracer bullet is story 1 (golden master): it runs the whole pipeline (data → three agents → mediator → fallback → log) for 38 rows and is the check every later story runs.
- Decision: 2026-11-02 — no closing "Refactor sweep" story: the epic is itself cleanup; epic-one-core closes with the sweep instead.
- Decision: 2026-11-03 — user: dev-only ruff (format + lint, autofix) and a GitHub Actions workflow running ruff and pytest on push and pull request (unblocks story 2).
- Decision: 2026-11-03 — user: archive `pitch.pptx`, the hackathon PDF, `atc-agent/agent-spec/` and `atc-agent/docs/` under `docs/hackathon/`; keep `.claude/skills/` as is; BMad skills stay local (unblocks story 5).
- Decision: 2026-11-03 — user: stories 2–5 are built by delegated subagents from one brief per story, each reviewed and merged by the orchestrator onto `refactor/safety-net-and-hygiene`; stories 1 and 6 by the orchestrator (`delegation-plan.md`).
- Decision: 2026-11-07 — user: run mode auto — stories 1 → 6 run without check-ins, stopping only on a stop condition in `delegation-plan.md`; the AGENTS.md block is reviewed at the end-of-epic pause.
- Decision: 2026-11-07 — Done-when and story 4 verify use `python -m autonomousprime.mediator.run`: the `autonomousprime run` CLI belongs to epic-one-core story 1.
