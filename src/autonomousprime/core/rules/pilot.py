"""The Pilot's hard rules: fuel margin and flight crew duty, both read off the Pilot's plan assessment."""

from autonomousprime.agents.constraints import fuel_crew_rules
from autonomousprime.agents.pilot.agent import assess_plan
from autonomousprime.core.contracts import Plan

from .registry import Rule, RuleContext


def _assessment(ctx: RuleContext):
    return ctx.memo("pilot", lambda: assess_plan("chk", Plan(**ctx.plan), ctx.scenario.pilot_inputs, fuel_crew_rules()))


def _fuel(ctx: RuleContext) -> str | None:
    a = _assessment(ctx)
    return None if a.fuel_ok else f"fuel margin {a.fuel_margin_min} min < 0"


def _duty(ctx: RuleContext) -> str | None:
    a = _assessment(ctx)
    return None if a.duty_ok else f"flight crew duty margin {a.duty_margin_min} min < 0"


RULES = [
    Rule("C-FUEL-1", "pilot", "hard", _fuel, "holding within the fuel available before the must-divert point"),
    Rule("C-CREW-2", "pilot", "hard", _duty, "flight crew duty within the legal limit"),
]
