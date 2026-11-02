---
type: epic
title: "Airborne flights hold within fuel on board and can divert"
parent: initiative-post-hackathon
covers: [R7]
after: [epic-known-gaps-closed]
refined: false
risk: medium
---

# Airborne flights hold within fuel on board and can divert

## Description

Lift the pre-departure-only assumption (constraints-audit L3, L4). An `airborne` scenario has no ground-delay lever: the menu offers holding up to the fuel on board before the must-divert point, plus diversion to the alternate (nearest airport > 100 nm, already computed). Diversion is an option the mediator and the fallback can choose, priced with the existing diversion weight and checked by the fuel and crew rules; cancellation remains a recommendation only. The console shows a diversion plan clearly, and evaluation includes airborne variants of the sample rows.

## Outcome

The duty manager gets a safe recommendation for a flight already in the air, including when the only safe answer is to divert.

## Done when

- An airborne row whose required holding exceeds its fuel produces a diversion plan that passes the checker and reaches the console.
- An airborne row with enough fuel holds instead, and the fuel margin is shown.
- MINIMUM_FUEL / EMERGENCY_FUEL flags change the fallback's choice as ADR-0002's follow-up specifies.
- RESULTS.md reports airborne rows separately.

## Boundaries

- Out: choosing among several alternates, en-route weather, real fuel-on-board data (synthetic, labelled).
- Belongs to epic-negotiation-beyond-three-rounds: the fallback's priority order itself.

## References

- parent — `_bmad-output/initiative-post-hackathon/initiative-post-hackathon.md`, R7
- constraints — `_bmad-output/initiative-post-hackathon/constraints-audit.md`, L3, L4, K6
- adr — `docs/adr/0002-safety-as-filter-not-cost.md`, Known gaps
- architecture — AD-3, AD-4, AD-5
