---
type: epic
title: "One disruption, every affected flight, one negotiation"
parent: initiative-post-hackathon
covers: [R11]
after: [epic-negotiation-beyond-three-rounds, epic-cascading-effects]
refined: false
risk: high
---

# One disruption, every affected flight, one negotiation

## Description

Bad weather hits every flight in its window, not one focal flight (design-register S4). This epic recovers them together, with epic-negotiation's N-party protocol and the authority model (N10).

The pattern follows a well-established real practice, the FAA ground delay program:
1. Traffic management allocates the reduced arrival slots in schedule order.
2. Each airline reassigns its own flights to its slots: swaps, extra delay, cancellation recommendations.
3. Ground fits gates.

A plan covers every affected flight, and its cascade comes from epic-cascading-effects.

Staged:
- **Stage 1:** the duty manager's airline brings all its affected flights; other airlines' flights take ATC's allocation.
- **Stage 2:** other airlines get their own agents.

The slot-allocation rules and fairness between airlines are decided in this epic's ADR.

## Outcome

The duty manager gets one plan for all their airline's flights hit by a disruption, with the knock-on for the rest of the day.

## Done when

- A weather hour at a hub produces one plan covering every affected flight of the duty manager's airline; it passes the checker, and its cascade is shown.
- Swapping two of the airline's flights between its slots is a proposal the airline agent can make, and code validates it.
- Cancellation appears only as a recommendation for the duty manager.

## Boundaries

- Not yet: network-wide re-routing or crew swaps across airports.

## References

- register — `_bmad-output/initiative-post-hackathon/design-register.md`, S1, S4, N10–N13
- architecture — AD-2, AD-6; spine "Deferred" (multi-flight)
