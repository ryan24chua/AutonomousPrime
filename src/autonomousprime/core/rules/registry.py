"""The rule registry: one registration per rule id, one place that evaluates the hard rules.

A `Rule` has an id (`C-FUEL-1`), an owner (the lane that stands behind it), a kind (`hard` or `soft`) and a
`check(ctx)` callable that returns the violation message, or None when the plan passes. `check()` runs the
hard rules in registration order and returns `"RULE-ID: message"` strings. Soft rules are registered so
their ids exist once, but they are never part of the pass/fail answer (they only cost and flag).

`RuleContext` holds the scenario and the plan and memoises what several rules share (the Pilot assessment,
Ground's check), so each lane's arithmetic runs once per plan however many rules read it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from autonomousprime.core.contracts import CheckResult


class RuleContext:
    """The scenario and one plan (a dict), plus a memo for values shared between rules."""

    def __init__(self, scenario: Any, plan: dict):
        self.scenario = scenario
        self.plan = plan
        self._memo: dict[str, Any] = {}

    def memo(self, name: str, compute: Callable[[], Any]) -> Any:
        if name not in self._memo:
            self._memo[name] = compute()
        return self._memo[name]


@dataclass(frozen=True)
class Rule:
    id: str
    owner: str
    kind: Literal["hard", "soft"]
    check: Callable[[RuleContext], str | None]
    summary: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("hard", "soft"):
            raise ValueError(f"rule {self.id}: kind must be 'hard' or 'soft', got {self.kind!r}")


_RULES: dict[str, Rule] = {}  # insertion order is the evaluation order


def register(rule: Rule) -> Rule:
    if rule.id in _RULES:
        raise ValueError(f"rule {rule.id} is already registered (owner {_RULES[rule.id].owner})")
    _RULES[rule.id] = rule
    return rule


def rules() -> list[Rule]:
    """Every registered rule, in evaluation order."""
    return list(_RULES.values())


def get(rule_id: str) -> Rule:
    return _RULES[rule_id]


def check(scenario: Any, plan: dict) -> CheckResult:
    """Run every hard rule on the plan, in registration order. A plan survives only if none is violated."""
    ctx = RuleContext(scenario, plan)
    violations = []
    for rule in _RULES.values():
        if rule.kind != "hard":
            continue
        message = rule.check(ctx)
        if message is not None:
            violations.append(f"{rule.id}: {message}")
    return CheckResult(not violations, violations)
