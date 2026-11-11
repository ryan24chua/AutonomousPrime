# ADR-0004: After the hackathon, only rules with a product reason stay invariants

**Status:** Accepted (11 Nov 2026). Amends ADR-0001 and ADR-0003; see their status lines.

## Context

The build was shaped by the Airbus challenge brief ([archived](../hackathon/challenge-2-brief.md)). Its "what to avoid" list and judging rubric became the project's invariants:
- three separate role calls;
- a deterministic fallback as the only exit;
- under three turns;
- an LLM that only chooses among code options.

So did the team's build-day rules: an Anthropic-SDK-only stack, one folder per owner, and replays as the stage-safe default.

The contest is over. A sweep of the repository on 11 Nov 2026 found about 290 places where these choices, or other choices nobody wrote down, limit where the project can go. They are grouped into 45 rows in [`design-register.md`](../../_bmad-output/initiative-post-hackathon/design-register.md), each with a ruling. This ADR records the rulings that change the project's rules.

## Decision

**Kept as product invariants.** Each has a reason that does not depend on the contest.

| Invariant | Reason |
|---|---|
| Code computes every number, checks every rule and decides termination and the pick. The LLM proposes, chooses and explains; code validates its proposals and recomputes every number. | LLMs are unreliable at arithmetic and legality; an audit needs reproducible numbers (LLM-Modulo). |
| Every negotiation is bounded and terminates in code; a deterministic fallback always exists. | The duty manager must get an answer in bounded time, with or without the LLM. |
| Safety is a filter, never a price ([ADR-0002](0002-safety-as-filter-not-cost.md)). | A hard rule traded for money is no longer a hard rule. |
| No hindsight: agents never see outcome columns. | Otherwise the evaluation measures leakage, not decisions. |
| A human approves or rejects every outcome; cancellation is only a recommendation. | Accountability stays with a qualified person. |
| Append-only log of every step; every synthetic input seeded and labelled. | Traceability and reproducibility. |

**Demoted to current design defaults.** They describe the design today. A change needs an ADR, not an exception.

| Default | Was | Register |
|---|---|---|
| Three roles (ATC, Pilot, Ground), each its own prompt and call, each seeing only its own facts. Roles become a registry. | Invariant "keep ATC, Pilot and Ground as separate prompts" | G1 |
| Agents choose among code-built options. Today every plan comes from ATC's arrival menu. | Invariant "the LLM only chooses among code-built options; any number it writes is ignored" | G3, N4 |
| A negotiation without consensus goes to the fallback, today after three rounds. A re-vote or an escalation to the human is allowed if bounded and decided by code. | Invariant "never in another agent turn" | G2 |
| LLM access goes through one gateway on the Anthropic SDK, with our own loop. | Policy "never an agent framework" | G4 |
| The current scope: an airline OCC duty manager at a US hub, one delayed arrival, the organisers' DOT 2015 file, a Streamlit console. | Initiative assumptions and "Out" lists | S1–S4, P4, P5 |
| The Nash-product pick ([ADR-0001](0001-nash-product-pick.md)). | "Good and should be kept" | N3 |

**Retired.**

| Rule | Register |
|---|---|
| The brief as "source of truth". It and the team's framing and agent agreement are now in `docs/hackathon/`. | G7 |
| Approve/Reject "in the console". Any front end may carry the human's decision. | G5 |
| "Tell the team" when the schema or rule ids change. A versioned contract and "a changed meaning gets a new id" remain. | G6 |
| A byte-identical golden master. It now pins plans, costs, outcomes, rule ids and round counts. A behaviour change lands as its own commit that states which numbers moved. | P1, P2 |
| "Live runs are the default when a key is present." A run is live only when the caller asks. | P7 |
| "Out" lists without a reason. Each is now "Not yet", with the trigger that brings it in. | P4 |

## Alternatives considered

| Option | Why not |
|---|---|
| Keep every brief rule as an invariant | It carries contest judging criteria into product decisions, which is the baggage this ADR removes. |
| Retire every brief rule | Several brief rules have real product reasons (the kept table). Dropping them would undo what makes the system trustworthy. |
| Rule on each choice only when an epic hits it | Every epic would re-argue the same rules. The register settles them once and leaves only the scope questions open. |

## Consequences

**Positive**
- An epic may change the roles, the protocol, the stack or the scope with one ADR, instead of fighting an invariant.
- The golden master stops freezing known bugs. Epic-one-core's world unification and the gate-world fixes can land with stated number changes.

**Negative**
- An invariant can no longer settle a design argument on its own authority; the default has to be defended on its merits.
- A narrower golden master no longer catches changes to reason text or decision-record wording; review has to.

## Follow-ups

- Settled in the register's second pass (11 Nov 2026), so none is open:
  - **Persona (S1):** the user stays the OCC duty manager. The agents are delegates of their organisations: traffic management, the airline's flight operations, and the airport and ground handler.
  - **Data (S2):** the full 2015 DOT file, fetched and checksummed, not in git (epic-full-2015-data).
  - **Several flights (S4):** recovering several flights at once and predicting cascading effects are in scope (epic-several-flights-at-once, epic-cascading-effects).
  - **Event size (S5):** the recorded delay stays the given disruption, labelled "known at decision time"; only the knock-on is predicted.
  - **Repo (G8, K1):** the AGENTS.md bmad markers are removed; a lockfile is added; run logs stay per-run JSONL files.
  - **Epic order (P6):** recorded in `tickets/tickets.toml`.
- Epic-negotiation's protocol ADR (ADR-0005) supersedes ADR-0003's fixed three rounds and keeps one of the two protocols in the code (register N2). It records four decisions already taken:
  - **N10, authority:** each organisation decides its own domain, and they negotiate where domains meet.
  - **N11, proposals:** agents make typed proposals that code validates.
  - **N12, sharing:** organisations share need, offer, interests, red lines, concessions and flags; raw data stays private.
  - **N13, no agreement:** the duty manager chooses between the two best plans, with the fallback computed.
