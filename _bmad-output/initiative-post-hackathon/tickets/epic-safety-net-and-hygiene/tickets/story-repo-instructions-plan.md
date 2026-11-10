---
title: 'Repo instructions describe the real project'
type: 'chore'
ticket: '6'
created: '2026-11-07'
status: 'done'
baseline_revision: '9be63c7'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: 'thorough'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `CLAUDE.md` is the hackathon file. It holds a Singapore team template with TBD sections, a 6-hour timeline, lane ownership and a greenfield MVP spec that the code has since outgrown. Every session loads it, so agents follow retired rules: ≤3 turns, one owner per folder, demo over quality.

**Approach:** Adopt the file with `bmad-project-context`.
- Archive it verbatim, so nothing is lost.
- Write a verified managed block in `AGENTS.md`, and make `CLAUDE.md` import it (`@AGENTS.md`).
- Carry every existing instruction through the ledger below.
- Trim `.env.example` to the one key the product uses.

## Boundaries & Constraints

**Always:**
- Every claim in the block names a path that exists or a command that was run.
- Every old instruction has a ledger decision.

**Never:**
- Delete an instruction without a ground. Grounds 1–3 ride the block approval; anything else waits for the user's line-item approval at the end-of-epic pause.

</frozen-after-approval>

## Code Map

- `CLAUDE.md` → `git mv` to `docs/hackathon/mvp-spec.md`, verbatim plus a two-line archive note. Code comments cite its sections. The name avoids `CLAUDE.md`, because a nested `CLAUDE.md` would load as live instructions.
- New `AGENTS.md`: the managed block (`<!-- bmad:context -->`), 56 lines, verified against 9be63c7.
- New `CLAUDE.md`: `@AGENTS.md`.
- `.env.example`: `ANTHROPIC_API_KEY` only. The four Singapore keys are gone; no code reads them.
- 23 comment and docstring citations of `CLAUDE.md §N` in `src/` and `app_prime.py` → `docs/hackathon/mvp-spec.md §N`. The exception is `evaluation/report.py`, which is generated `RESULTS.md` text and is deferred.
- `docs/hackathon/README.md`: adds a line for `mvp-spec.md`.

## Ledger: where each instruction in the old CLAUDE.md went

Grounds: 1 stale or incorrect · 2 mechanically enforced · 3 harmful or contradictory · 4 user-approved. "Plan" means the delegation plan the user approved on 2026-11-03: "Remove the hackathon timeline, lanes and the Singapore template".

| Old instruction | Decision | Where / why |
|---|---|---|
| Template header and goal ("one agent … Singapore task … six-hour hackathon … optimise for a working demo") | delete | Ground 4 (plan: Singapore template) and ground 1: the product is not a Singapore task, and the hackathon is over (constraints-audit X5). |
| Problem paragraph | rewrite | Orientation. "≤3 turns" becomes the invariant "every negotiation terminates in code" (X1 retired the number, K3 keeps the intent). |
| Stack TBD, candidates Next.js/FastAPI | delete | Ground 1: the stack is chosen (Python 3.13, Streamlit, Anthropic SDK) and is stated in Orientation. |
| Roles: one owner per folder, don't edit another person's folder | delete | Ground 4 (plan: lanes) and ground 3: it caused four world builders and three cost tables (constraints-audit X4). |
| Contracts: schema, log format and rule IDs defined in framing §4–5; change only there, in their own commit; tell the team | rewrite | Policy line. The current definitions live in code and `docs/architecture.md` §5–6, so the pointer moved there. "Own commit" and "tell the team" are kept. |
| Models: Haiku for bulk, Sonnet default, Opus for one hard step; cache system prompt and tools | rewrite, narrowed | Conventions: agents use `claude-sonnet-5-5` with `max_tokens` and cached system prompts (verified in all three agents). Haiku/Opus guidance dropped: no code path uses them. Approved by user 2026-11-10 (ground 4). |
| Never commit keys; `.env.local`; add names to `.env.example` | retain | Policy (K9). |
| Irreversible actions (send, submit, pay) wait for the user's approval click | rewrite | Invariant "a human decides: Approve/Reject is the decision; cancellation only a recommendation" (K6). Send/pay do not exist in this product. |
| No Singpass, CAPTCHAs or logins in the demo path | delete | Ground 1: no such path exists (Singapore template). |
| Seed demo data and cache flaky responses | rewrite / automate | Seeding lives in the invariant "seed and label every synthetic input" (K8). The replay path is enforced by `tests/unit/ui/test_console.py` (ground 2). |
| Commit small, `git pull --rebase` before pushing, keep `main` deployable | retain | Policy. |
| Skip test-first TDD; verify the change actually works before saying it's done | retain | Running and verifying. |
| §1 Event and deadlines (16:15, 15:45, 3-min pitch) | delete | Ground 4 (plan: timeline) and ground 1: past. |
| §2 Challenge essentials (structured messages, constraint checking, log, fallback, ≤3 turns, avoid merged roles / unbounded loops / ignoring safety) | rewrite | The kept intents are the Product invariants (K1–K4, K7). "≤3 turns" retired (X1). |
| §3 Rubric weights | delete | Ground 1: the hackathon rubric no longer scores anything (constraints-audit X10). Kept in `docs/challenge-2-brief.md` and the archive. Approved by user 2026-11-10 (ground 4). |
| §4 Scope: two events, three decisions, pre-departure default, 3 agents, passive background flights, out-of-scope list | relocate | `docs/architecture.md` §1–3 describes what is built. The out-of-scope list is now the initiative's roadmap (epics 4–6). The archive keeps the text. |
| §5 Workflow and middle-man pseudocode; invalid plans hidden; re-ask once then reject | relocate | `docs/architecture.md` §3–4, ADR-0003, and the code (`mediator/core.py`). The termination intent is in the invariants. |
| §6 World-state table and fuel formula | relocate | `docs/architecture.md` §6–7 and `docs/challenge-2-framing.md` §6. "No hindsight" is retained verbatim as an invariant (K5). |
| §7 Agents table, MINIMUM_FUEL red line, message schema, independence | relocate | `docs/architecture.md` §5 and `docs/agent-alignment.md`. The red line is code (`agents/constraints.py`, `minimum_fuel_margin_min`). |
| §8 Constraint checker | relocate | `docs/architecture.md` §6. Safety-as-filter is an invariant (K4). |
| §9 Cost model | relocate | `docs/architecture.md` §7. The three duplicated weight tables are flagged in Where things are. |
| §10 Fallback solver | relocate | `docs/architecture.md` §2, `fallback/scenario.py`. Invariant K3. |
| §11 Consensus log | relocate | `docs/architecture.md` §9. Invariant K7. |
| §12 Document crafter (LLM narrative) | delete | Ground 1: not built ("Not built" in RESULTS.md §1). It is an epic-6 option, not current state. |
| §13 Evaluation (~30 rows, metrics, show a failure, cache LLM responses); demo scenario DFW 24 Apr 2015 | relocate | `docs/RESULTS.md` and `evaluation/evaluate.py`. The rewrite pitfall is in Running and verifying. |
| §14 Models (Sonnet tier; confirm IDs; set `max_tokens`) | rewrite | Merged into the Conventions line. |
| §15 Stack and layout TODO; suggested modules; `.env.example`; no agent frameworks | rewrite | Where things are lists the real modules. "No agent frameworks" moved to Policy (K10). |
| §16 Roles A–D | delete | Ground 4 (plan: lanes). |
| §17 Timeline | delete | Ground 4 (plan: timeline). |
| §18 Never put arithmetic, scheduling or legality checks in a prompt | retain | Invariant (K1). |
| §18 Never merge agent roles; one call per agent per round | retain | Invariant (K2). |
| §18 Simplest end-to-end first (terminal), then UI | delete | Ground 1: both exist. A build-order hint for an empty repo. Approved by user 2026-11-10 (ground 4). |
| §18 Log every LLM call during development | rewrite | Invariant "log every step to the consensus log". Agents also log their own calls (`logs/atc/`, the Ground log path). Narrowed; approved by user 2026-11-10 (ground 4). |
| §18 If something is ambiguous enough to change the design, ask before building | delete | A platitude: asking on design-changing ambiguity is the default. Approved by user 2026-11-10 (ground 4). |
| §18 Ask before adding dependencies or external services | retain | Policy. |

New lines (not in the old file):
- Branch naming: user, 2026-11-02.
- Golden-master rule: AD-11.
- Editable install: `paths.py`.
- `pytest` scope and the live marker: `pyproject.toml`.
- `docs/hackathon/` is not current rules.
- Pitfalls:
  - `negotiate()` and `make_cache.py` go live when a key is set. Observed this session; the golden master had to pass `live=False`.
  - The `flights.csv` re-read cost. Measured: 8.6 s of a 9.2 s run.

## Implementation Notes

- Built by the orchestrator, not delegated: the skill is conversational and the user approves instruction writes.
- Auto mode (2026-11-07): the block is committed on `refactor/safety-net-and-hygiene` for review at the end-of-epic pause. It is not on `main`; a PR to `main` was opened at the end-of-epic pause (2026-11-10).
- Verification:
  - Every backticked path in the block exists; the only non-paths are column names and bare filenames the block also gives in full.
  - Commands named:
    - `pytest` (34–38 s): run.
    - `pytest -m live`: run, skipped without a key.
    - `python -m autonomousprime.mediator.run`: run at the end-of-epic check.
    - `python -m tests.golden.update`: run in story 1.
  - The ticket's grep for `TBD|Singapore|Singpass|15:00|one owner per folder` in `CLAUDE.md` and `AGENTS.md` is empty.

## Review Triage Log

- 2026-11-10: user approved all five ground-4 ledger rows (Haiku/Opus guidance narrowed, §3 rubric, §18 simplest end-to-end first, §18 log every LLM call narrowed, §18 ask if ambiguous) and the `AGENTS.md` block as committed in d7b0692. No changes requested.

## Verification

**Commands:**
- `grep -nE "TBD|Singapore|Singpass|15:00|one owner per folder" CLAUDE.md AGENTS.md` -- expected: empty. Done: empty.
- `pytest -q` -- expected: 75 passed, 1 deselected, snapshot unchanged. Done.
- `ruff check . && ruff format --check .` -- expected: clean. Done.
