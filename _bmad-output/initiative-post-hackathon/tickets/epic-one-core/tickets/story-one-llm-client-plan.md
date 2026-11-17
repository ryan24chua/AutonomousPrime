---
title: 'One LLM client and agent template'
type: 'refactor'
ticket: '7'
created: '2026-11-17'
status: 'in-review'   # code merged; the live demo-row check (hitl) is pending
baseline_revision: '5b7648b (rebased onto d7574d6)'
route: 'full'
risk: 'medium'
review: 'quick'
review_loop_iteration: 0
built_by: 'subagent (worktree)'
deferred:
  - 'LIVE CHECK PENDING (hitl): run `pytest -m live` (or one live `python -m autonomousprime run --live`) with a key. Not verifiable here:
    - the SDK accepting ATCOutput (Literal flags, None gate, "from" alias) in messages.parse;
    - real usage and request_id fields;
    - effort and output_format together for ATC;
    - real exception classes in the retry mapping.'
  - 'DECISION FOR THE USER: the response cache is now on by default for every live run (Pilot and Ground included, not only ATC). `make_cache.py --live` and the console live button return a cached answer for an identical request. Delete `.cache/llm` or pass cache=False to force fresh calls.'
  - 'ATC''s old cache files in .cache/atc are no longer read. ATC keeps its own per-turn log in logs/atc/.'
  - 'Prompts still hard-code word limits (see story 4). They now load at call time, so rendering them from contracts.LIMITS is a small follow-up (story 11).'
---

## Intent

Each agent called the API its own way:
- ATC: sync client, free-text JSON, its own `.env` reader and cache;
- Pilot and Ground: async `messages.parse`, each with its own loop and log.

`anthropic` was imported in seven modules (design-register G4).

## What landed (`d1ca50d`)

- **`infra/llm.py`:**
  - `LLMGateway.parse` returns a typed `LLMResult.kind`: ok, refusal, max_tokens, no_output, invalid, transient_error or api_error.
  - The system prompt is cached (breakpoint on the last block). Transient errors get one retry.
  - A disk response cache under `.cache/llm` (failures never cached) and a JSONL call log `logs/llm_calls.jsonl` (no message text).
  - `ROLE_SETTINGS`: every role on claude-sonnet-5-5; ATC 700 tokens; Pilot and Ground 4000 tokens with effort medium.
  - `make_client`, `make_gateway`, `as_gateway`. `service.LiveUnavailable` is the gateway's class.
- **`agents/base.py`:** `RoleAgent.run_turn` is the shared correction loop, bounded by `LIMITS.max_attempts`. Prompts load at call time.
- **ATC, Pilot and Ground moved onto it.**
  - ATC is async and uses `messages.parse` with an output model mirroring its dict contract.
  - ATC's dry path is byte-identical.
- **SDK imports:** only `infra/llm.py` imports `anthropic`, and lazily, so a dry run loads no SDK. Both are enforced by tests.
- **Behaviour changes, live path only:**
  - ATC API errors become rejects instead of exceptions.
  - The Pilot's schema-invalid replies take the correction loop instead of raising.
  - ATC's off-set flags fail at schema parsing and take the correction path.
  - Every final give-up is still a reject.

## Verification

- Subagent: pytest gives 182 passed, 1 deselected. ruff, format and lock are clean; the no-SDK subprocess test passes; the grep test passes.
- Orchestrator, after rebasing onto story 5:
  - pytest: 190 passed, 1 deselected;
  - ruff and format clean;
  - snapshot, `pyproject.toml` and `uv.lock` unchanged;
  - `grep import anthropic src` finds only `infra/llm.py`.
