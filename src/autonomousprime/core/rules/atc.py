"""ATC's hard rule: the plan must be on the arrival menu code computed (arrival cap, wake spacing)."""

from autonomousprime.agents.atc.menu import check_slot

from .registry import Rule, RuleContext


def _cap(ctx: RuleContext) -> str | None:
    slot = check_slot({**ctx.plan, "gate": None}, ctx.scenario.atc_menu)
    prefix = "C-CAP-1: "
    for v in slot["violations"]:
        if v.startswith(prefix):
            return v[len(prefix) :]
    return None


RULES = [
    Rule("C-CAP-1", "atc", "hard", _cap, "arrivals per hour within the cap; plan on ATC's computed menu"),
]
