"""The one place hard rules are registered and evaluated (docs/architecture.md section 6).

Each owner module lists its `RULES`; they are registered here in a fixed order, and `check(scenario, plan)`
reports violations in that order: C-CAP-1 (ATC), C-FUEL-1, C-CREW-2 (Pilot), then Ground's C-TURN-1,
C-GATE-1, C-GATE-2. Soft rules (C-CREW-1) are registered but never filter.
"""

from . import atc, ground, pilot
from .registry import Rule, RuleContext, check, get, register, rules

for _module in (atc, pilot, ground):  # evaluation order
    for _rule in _module.RULES:
        register(_rule)

__all__ = ["Rule", "RuleContext", "check", "get", "register", "rules"]
