"""The rule registry (core/rules): one registration per id, one fixed evaluation order, ids only there."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from autonomousprime import paths
from autonomousprime.agents.ground.checker import Check, GroundCheck, Violation
from autonomousprime.core import rules
from autonomousprime.core.rules import atc as atc_rules
from autonomousprime.core.rules import ground as ground_rules
from autonomousprime.core.rules import pilot as pilot_rules

SRC = Path(paths.REPO) / "src" / "autonomousprime"
ARCHITECTURE = Path(paths.REPO) / "docs" / "architecture.md"
ID = re.compile(r"C-[A-Z]+-\d")

# Rows of architecture.md section 6 that no code checks: wake spacing is built into ATC's menu times.
NOT_CHECKED_IN_CODE = {"C-WAKE-1", "C-SEP-1"}


def _documented_ids() -> set[str]:
    ids = set()
    for line in ARCHITECTURE.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `C-"):
            ids |= set(ID.findall(line.split("|")[1]))
    return ids - NOT_CHECKED_IN_CODE


def test_every_documented_rule_is_registered_exactly_once():
    registered = [r.id for r in rules.rules()]
    assert len(registered) == len(set(registered))
    assert set(registered) == _documented_ids()


def test_kinds_and_owners():
    by_id = {r.id: r for r in rules.rules()}
    assert by_id["C-CREW-1"].kind == "soft"
    assert all(r.kind == "hard" for i, r in by_id.items() if i != "C-CREW-1")
    assert by_id["C-CAP-1"].owner == "atc"
    assert by_id["C-PLAN-1"].owner == "mediator"
    assert by_id["C-FUEL-1"].owner == by_id["C-CREW-2"].owner == "pilot"
    assert {by_id[i].owner for i in ("C-TURN-1", "C-GATE-1", "C-GATE-2", "C-CREW-1")} == {"ground"}


def test_registering_a_duplicate_id_raises():
    with pytest.raises(ValueError, match="already registered"):
        rules.register(rules.Rule("C-FUEL-1", "pilot", "hard", lambda ctx: None))


def test_a_rule_kind_must_be_hard_or_soft():
    with pytest.raises(ValueError):
        rules.Rule("C-X-1", "atc", "medium", lambda ctx: None)  # type: ignore[arg-type]


# Rule ids may be written as string literals only in core/rules, except in these files, which keep them for
# a reason that is not "deciding a plan": lane checkers return structured results the agents read, and prose
# names rules for people. Nothing on the mediator's path emits an id except through the registry.
ALLOWED_LITERALS = {
    "agents/atc/menu.py": "check_slot returns ATC's structured check (rule_id C-CAP-1) for the ATC agent's table",
    "agents/ground/checker.py": "check_ground returns Violation/Check records keyed by rule id (Ground's own result)",
    "agents/ground/icap.py": "Ground's ICAP summary lists its rule ids for the Ground agent's facts",
    "mediator/adapters.py": "one human-readable score reason names C-CAP-1 (prose, not a check)",
    "evaluation/evaluate.py": "reads C-FUEL-1 back out of violation strings to count an ablation",
    "evaluation/report.py": "published prose that names the rules",
}


def _files_with_id_literals() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC).as_posix()
        if rel.startswith("core/rules/"):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and ID.search(node.value):
                found.setdefault(rel, []).extend(ID.findall(node.value))
    return found


def test_rule_id_literals_live_only_under_core_rules():
    found = _files_with_id_literals()
    outside = sorted(set(found) - set(ALLOWED_LITERALS))
    assert not outside, f"rule ids written outside core/rules: {outside}"
    assert set(ALLOWED_LITERALS) <= set(found), "an allowed exception no longer has a literal; drop it from the list"


def _scenario():
    return SimpleNamespace(atc_menu=[], pilot_inputs=None, ground_state=None)


def _plan(gate="C14"):
    return {
        "arrival_slot": "20:00",
        "ground_delay_min": 0,
        "holding_min": 0,
        "extra_fuel_min": 0,
        "gate": gate,
        "divert": False,
    }


def _all_failing(monkeypatch):
    monkeypatch.setattr(atc_rules, "check_slot", lambda plan, menu: {"violations": ["C-CAP-1: not on the menu"]})
    monkeypatch.setattr(
        pilot_rules,
        "assess_plan",
        lambda *a: SimpleNamespace(fuel_ok=False, fuel_margin_min=-3, duty_ok=False, duty_margin_min=-7),
    )
    violations = [Violation(i, f"{i} broke", {}) for i in ("C-TURN-1", "C-GATE-1", "C-GATE-2")]
    checks = [Check("C-CREW-1", True, "overtime", {"overtime_min": 20})]
    monkeypatch.setattr(ground_rules, "check_ground", lambda p, s: GroundCheck(False, violations, checks))


def test_check_reports_violations_in_the_documented_order(monkeypatch):
    _all_failing(monkeypatch)
    res = rules.check(_scenario(), _plan())
    assert not res.valid
    assert res.violations == [
        "C-CAP-1: not on the menu",
        "C-FUEL-1: fuel margin -3 min < 0",
        "C-CREW-2: flight crew duty margin -7 min < 0",
        "C-TURN-1: C-TURN-1 broke",
        "C-GATE-1: C-GATE-1 broke",
        "C-GATE-2: C-GATE-2 broke",
    ]


def test_a_plan_without_a_gate_skips_the_other_ground_rules(monkeypatch):
    _all_failing(monkeypatch)
    res = rules.check(_scenario(), _plan(gate=None))
    assert [v.split(":")[0] for v in res.violations] == ["C-CAP-1", "C-FUEL-1", "C-CREW-2", "C-PLAN-1"]
    assert res.violations[-1] == "C-PLAN-1: no gate in plan"


def test_a_passing_plan_is_valid_and_soft_rules_never_filter(monkeypatch):
    monkeypatch.setattr(atc_rules, "check_slot", lambda plan, menu: {"violations": []})
    monkeypatch.setattr(
        pilot_rules,
        "assess_plan",
        lambda *a: SimpleNamespace(fuel_ok=True, fuel_margin_min=5, duty_ok=True, duty_margin_min=9),
    )
    checks = [Check("C-CREW-1", True, "overtime 20", {"overtime_min": 20})]
    monkeypatch.setattr(ground_rules, "check_ground", lambda p, s: GroundCheck(True, [], checks))
    res = rules.check(_scenario(), _plan())
    assert res.valid and res.violations == []
