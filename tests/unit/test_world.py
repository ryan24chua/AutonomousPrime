"""core.world: one frozen WorldState per negotiation, each role reading only its own view."""

import dataclasses

import pytest

from autonomousprime import service
from autonomousprime.core import world as core_world
from autonomousprime.core.world import GroundState, PilotInputs, World, WorldState
from autonomousprime.mediator import adapters
from autonomousprime.service import FlightKey, build_world_for

DEMO = FlightKey(2015, 4, 24, "AA", "1480", "MCI")  # DFW weather row used by the console

# What only one role may see. A view must not carry another role's private inputs.
PRIVATE = {
    "atc": {"background", "weather_hours", "weather_cut", "focal_earliest_arr_min"},
    "pilot": {"alternate", "connections", "crew_report", "mct_min", "aircraft_class"},
    "ground": {
        "gate_busy",
        "scheduled_gate",
        "crew_shift_start_min",
        "connecting_pax",
        "connection_slack_min",
        "now_min",
    },
}
VIEW_TYPES = {"atc": World, "pilot": PilotInputs, "ground": GroundState}


@pytest.fixture(scope="module")
def demo_world() -> WorldState:
    return build_world_for(DEMO, seed=7)


@pytest.mark.parametrize("role", list(VIEW_TYPES))
def test_view_excludes_other_roles_private_fields(role):
    names = {f.name for f in dataclasses.fields(VIEW_TYPES[role])}
    assert PRIVATE[role] <= names, f"{role} view lost its own fields"
    for other, private in PRIVATE.items():
        if other != role:
            assert not names & private, f"{role} view carries {other}'s private fields {names & private}"


def test_views_and_provenance(demo_world):
    for role, cls in VIEW_TYPES.items():
        assert isinstance(demo_world.view(role), cls)
    with pytest.raises(KeyError):
        demo_world.view("mediator")
    assert demo_world.negotiation_id == "DFW-20150424-AA1480"
    prov = demo_world.provenance
    for role in VIEW_TYPES:
        assert any(k.startswith(f"{role}: ") for k in prov), f"no provenance for {role}"
    assert all(v for v in prov.values())


def test_world_state_is_frozen(demo_world):
    with pytest.raises(dataclasses.FrozenInstanceError):
        demo_world.seed = 8


def test_focal_carries_no_hindsight(demo_world):
    from autonomousprime.infra.data import OUTCOME_COLUMNS

    assert not set(OUTCOME_COLUMNS) & set(demo_world.focal)


def test_build_world_runs_once_per_negotiate(monkeypatch):
    calls = []
    real = core_world.build_world

    def counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(adapters, "build_world", counting)
    result = service.negotiate(DEMO, seed=7, live=False)
    try:
        assert len(calls) == 1
    finally:
        from pathlib import Path

        Path(result.log_path).unlink(missing_ok=True)


@pytest.mark.parametrize(
    "key",
    [DEMO, FlightKey(2015, 4, 24, "AA", "96", "STL")],  # weather, late aircraft (console demo rows)
    ids=["weather", "late_aircraft"],
)
def test_every_view_shares_one_disrupted_arrival(key):
    w = build_world_for(key, seed=7)
    assert w.ground.disrupted_arrival_min == w.atc.focal_earliest_arr_min
    assert w.ground.now_min == w.ground.disrupted_arrival_min - 60
    assert w.ground.event_end_min == w.ground.scheduled_arrival_min + w.ground.event_magnitude_min


def test_every_view_uses_one_event_classifier(demo_world):
    from autonomousprime.core.world import event_of

    event = event_of(demo_world.focal)
    assert demo_world.atc.event == event
    assert (demo_world.pilot.event_type, demo_world.pilot.event_magnitude_min) == (
        event["type"],
        event["magnitude_min"],
    )
    assert (demo_world.ground.event_type, demo_world.ground.event_magnitude_min) == (
        event["type"],
        event["magnitude_min"],
    )


def test_world_refuses_rows_from_another_date():
    from autonomousprime.core.world import build_world
    from autonomousprime.infra import data

    rows = data.day(2015, 4, 24)
    focal = next(r for r in rows if (r["AIRLINE"], r["FLIGHT_NUMBER"], r["ORIGIN_AIRPORT"]) == ("AA", "1480", "MCI"))
    with pytest.raises(ValueError, match="another|dated"):
        build_world(rows + data.day(2015, 4, 25)[:1], focal, seed=7)


def test_synthetic_draws_are_keyed_per_flight():
    a = build_world_for(DEMO, seed=7)
    b = build_world_for(FlightKey(2015, 4, 24, "AA", "36", "SAN"), seed=7)  # same airport (DFW), same day
    assert a.ground.airport == b.ground.airport
    spares = lambda w: [g for g, busy in w.ground.gate_busy.items() if not busy]  # noqa: E731
    assert spares(a) != spares(b), "two flights must not share the same synthetic gate world"
    assert spares(build_world_for(DEMO, seed=7)) == spares(a), "same flight and seed must repeat exactly"


SMALL_HUB = FlightKey(2015, 4, 24, "AA", "71", "DFW")  # -> SJC, 30 gates (one terminal)
NON_HUB = FlightKey(2015, 4, 24, "AA", "125", "DFW")  # -> PNS, 8 gates


@pytest.mark.parametrize("key", [SMALL_HUB, NON_HUB], ids=["small_hub", "non_hub"])
def test_gate_world_works_at_any_airport_size(key):
    g = build_world_for(key, seed=7).ground
    assert g.limits.size_class in ("Small hub", "Non-hub")
    assert len(g.gate_busy) == g.limits.gates
    assert g.scheduled_gate in g.gate_busy
    spares = [gate for gate, busy in g.gate_busy.items() if not busy]
    assert spares and g.scheduled_gate not in spares


def test_non_hub_negotiates_end_to_end():
    from pathlib import Path

    result = service.negotiate(NON_HUB, seed=7, live=False)
    Path(result.log_path).unlink(missing_ok=True)
    assert result.outcome in ("consensus", "halt_least_cost", "recommend_cancel")
