"""Ground's rules, read off `check_ground` (the arithmetic stays in agents/ground/checker.py).

Ground checks a plan only when it names a gate. A plan without one is refused by C-PLAN-1 (core/rules/plan.py)
and Ground's rules stay silent.
"""

from autonomousprime.agents.ground.checker import check_ground
from autonomousprime.core.contracts import Plan

from .registry import Rule, RuleContext


def _ground(ctx: RuleContext):
    if ctx.plan.get("gate") is None:
        return None
    return ctx.memo("ground", lambda: check_ground(Plan(**ctx.plan), ctx.scenario.ground_state))


def _violation(rule_id: str):
    def check(ctx: RuleContext) -> str | None:
        g = _ground(ctx)
        if g is None:
            return None
        return next((v.message for v in g.violations if v.rule_id == rule_id), None)

    return check


def _crew_overtime(ctx: RuleContext) -> str | None:
    g = _ground(ctx)
    c = next((c for c in g.checks if c.rule_id == "C-CREW-1"), None) if g else None
    return c.detail if c and c.values.get("overtime_min") else None


RULES = [
    Rule("C-TURN-1", "ground", "hard", _violation("C-TURN-1"), "turnaround at least the airport minimum"),
    Rule("C-GATE-1", "ground", "hard", _violation("C-GATE-1"), "gate free within the wait cap for the turnaround"),
    Rule("C-GATE-2", "ground", "hard", _violation("C-GATE-2"), "gate change with enough notice"),
    Rule("C-CREW-1", "ground", "soft", _crew_overtime, "ground crew overtime (cost and flag, not a filter)"),
]
