---
type: epic
title: "Agents negotiate in every round under a configurable, bounded policy"
parent: initiative-post-hackathon
covers: [R5]
after: [epic-one-core]
refined: false
risk: high
---

# Agents negotiate in every round under a configurable, bounded policy

## Description

Retire the fixed "exactly three rounds, Claude votes only in round 3" (constraints-audit X1, X6) while keeping bounded, code-decided termination (K3). `NegotiationPolicy` holds the round cap, deadline and LLM-call budget; the mediator loops until unanimous acceptance of a checked plan or a stop condition, then falls back. Claude proposes, scores and votes in every round, by option id from code-computed menus or with a typed proposal that code validates (AD-1 as amended 2026-11-11). Agents can concede (relax a stated bound, framing §3); code checks the relaxed bound. The two protocols in the code today (the agent folders' propose/accept/counter/reject and the mediator's shortlist/score/vote) become one, and the agents' need, offer, flags and counters reach the mediator instead of being reduced to accept/reject (design-register N2). Agents see the pick rule's reasoning before voting, so vote and pick no longer disagree by construction (RESULTS §5.5). Scores come from each role's real utility normalised to its range and measured against the fallback plan (ADR-0001 follow-up). The fallback ranks by safety priority before cost: EMERGENCY_FUEL → earliest slot, MINIMUM_FUEL → no added holding, prefer ≥ 10 min fuel margin, exclude Pilot safety rejections, then cheapest (ADR-0002 follow-up). ADR-0005 records the new protocol and supersedes ADR-0003.

## Outcome

The recommendation reflects what the three agents argued, not only what the code ranked, and the protocol's limits are settings rather than code.

## Done when

- Each behaviour change (vote/pick alignment, the fallback's safety order, the merged protocol) is its own commit that updates the golden master and states which numbers moved; with live agents, every round's call log shows one call per agent.
- Raising `max_rounds` changes the consensus rate on the evaluation sample, and RESULTS.md reports it per setting with LLM calls per run.
- No evaluated run exceeds its policy's budget; every non-consensus ends in the fallback.
- ADR-0005 merged; ADR-0003 marked superseded.
- An ablation (single prompt playing all three roles; checker off) is reported, showing why separate agents and the checker matter.

## Boundaries

- Not yet: multi-flight negotiation (several Pilot agents) — open question at the initiative (design-register S4).
- Must not change: AD-1 (code validates every proposal and computes every number), AD-3 (safety filter before cost).

## References

- parent — `_bmad-output/initiative-post-hackathon/initiative-post-hackathon.md`, R5
- register — `_bmad-output/initiative-post-hackathon/design-register.md`, G2, G3, N1, N2, N3, P3
- adr — `docs/adr/0001…0003`, Follow-ups
- framing — `docs/hackathon/challenge-2-framing.md` §3 (monotonic concession)
- architecture — AD-1, AD-2, AD-6
