"""The mediator's own hard rule: every plan names a gate.

Ground's rules read a gate; a plan with none never reaches them (core/rules/ground.py stays silent), so this
rule is what refuses it. It used to be reported as C-GATE-1, which means something else (gate availability).
"""

from .registry import Rule, RuleContext


def _names_a_gate(ctx: RuleContext) -> str | None:
    return "no gate in plan" if ctx.plan.get("gate") is None else None


RULES = [
    Rule("C-PLAN-1", "mediator", "hard", _names_a_gate, "every plan names a gate"),
]
