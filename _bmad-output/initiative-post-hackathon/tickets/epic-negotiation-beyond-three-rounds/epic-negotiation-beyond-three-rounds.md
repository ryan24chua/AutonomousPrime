---
type: epic
title: "Organisations' agents negotiate in every round under a bounded policy"
parent: initiative-post-hackathon
covers: [R5]
after: [epic-one-core, epic-plans-time-and-events, epic-cascading-effects]
refined: false
risk: high
---

# Organisations' agents negotiate in every round under a bounded policy

## Description

Today's negotiation is mostly code (design-register N1, N2):
- Code proposes and ranks every plan, and the scores are rank positions.
- Claude only accepts or rejects one picked plan, in round 3.
- The agents' prompts ask for counters, interests and red lines, but the mediator passes `others=[]`, keeps only accept/reject, and counts a counter as a reject.
- In the dry run on 24 Apr 2015 (MQ3086), the Pilot's three favourite slots died on the synthetic gate A12, and no agent could say "same slot, other gate".

This epic replaces that with the pipeline the user chose on 2026-11-11 (register N10–N13):

- **Agents are organisations' delegates.** ATC is the airport's traffic management, the airline is its flight operations (today's Pilot), and Ground is the airport and ground handler. Each holds only its organisation's data and objectives.
- **Authority model (N10).** Each organisation decides its own domain: ATC sets capacity (slots and separation are not bargained over), the airline chooses among those slots for its flights, and Ground fits gates. Negotiation happens where domains meet, for example priority for a low-fuel flight, or a later slot for a free gate. Agreement means every organisation accepts the parts of the plan in its domain.
- **A real, bounded loop.** `NegotiationPolicy` holds the round cap, deadline and LLM-call budget (default three rounds). In every round each agent makes one LLM call: it reads its private view, the table and the other parties' public messages, then returns a typed message.
- **Typed proposals (N11).** Within its own levers an agent may accept or reject plans, propose ("swap two flights' slots", "use gate C12"), or concede ("accept 15 more minutes"). Code validates every proposal against the hard rules and recomputes every number; picking among code options stays possible.
- **What is shared (N12).** Need, offer, interests, red lines, concessions and flags reach the other parties; raw data (fuel figures, crew rosters, gate bookings) stays private. Concessions are monotonic. The two protocols in the code today become one (N2).
- **Without agreement (N13).** The deterministic fallback is still computed and logged, ranked safety first: EMERGENCY_FUEL → earliest slot, MINIMUM_FUEL → no added holding, prefer ≥ 10 min fuel margin, exclude Pilot safety rejections, then cheapest (ADR-0002 follow-up). The duty manager sees the two best checked plans and each organisation's objection, then chooses, approves the fallback or rejects.
- **Scores (ADR-0001 follow-up).** Where code still ranks acceptable plans, scores are each role's real utility, normalised and measured against the fallback; vote and pick no longer disagree by construction (RESULTS §5.5).

ADR-0005 records the protocol and supersedes ADR-0003. It is built for N parties so that epic-several-flights-at-once adds flights and airlines without a new protocol.

## Outcome

The recommendation reflects what each organisation argued and conceded, every number in it is code's, and when they disagree the duty manager sees the disagreement and decides.

## Done when

- With live agents, every round's call log shows one call per organisation, and at least one evaluated run reaches agreement through a validated proposal or concession, not a code pick.
- The MQ3086 case above can be repaired: an agent proposes the same slot at another gate, and code accepts it if it passes the rules.
- A run without agreement shows the duty manager two checked plans with each organisation's objection, and the fallback is in the log.
- No evaluated run exceeds its policy's budget.
- Each behaviour change (vote/pick alignment, the fallback's safety order, the merged protocol) is its own commit that updates the golden master and states which numbers moved.
- An ablation (one prompt playing all roles; checker off) is reported, showing why separate agents and the checker matter.
- ADR-0005 merged; ADR-0003 marked superseded.

## Boundaries

- Belongs to epic-several-flights-at-once: more than one flight and more than one airline. This epic builds the protocol for N parties and runs it on one flight.
- Must not change: AD-1 (code validates every proposal and computes every number), AD-3 (safety filter before cost), the human decides.

## References

- parent — `_bmad-output/initiative-post-hackathon/initiative-post-hackathon.md`, R5, R11
- register — `_bmad-output/initiative-post-hackathon/design-register.md`, G2, G3, N1, N2, N3, N10–N13, P3
- adr — `docs/adr/0001…0004`, Follow-ups
- framing — `docs/hackathon/challenge-2-framing.md` §3 (monotonic concession)
- architecture — AD-1, AD-2, AD-6

## Notes

- Decision: 2026-11-11 — user: authority model (N10), typed proposals validated by code (N11), shared need/offer/interests/red lines/concessions/flags with raw data private (N12), and without agreement the duty manager chooses between the two best checked plans with the fallback computed (N13).
