"""service.negotiate: live is explicit and fails early without a key; FlightKey round-trips a demo row."""

import inspect

import pytest

from autonomousprime import cli, service
from autonomousprime.service import FlightKey, LiveUnavailable
from demo_rows import DEMO_ROWS, row_date


@pytest.fixture
def no_key(monkeypatch):
    """No API key, and no .env.local can supply one; building a scenario is a test failure."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(service, "load_dotenv", lambda *a, **k: None)

    def fail(*a, **k):
        raise AssertionError("build_scenario must not run when live mode is unavailable")

    monkeypatch.setattr(service, "build_scenario", fail)


def test_live_without_key_raises_before_building(no_key):
    key = FlightKey(2015, 4, 24, "AA", "36", "SAN")
    with pytest.raises(LiveUnavailable, match="ANTHROPIC_API_KEY"):
        service.negotiate(key, live=True)


def test_cli_live_without_key_exits_2(no_key, monkeypatch, capsys):
    # find_flight reads the day's rows; stub it so this stays fast.
    monkeypatch.setattr(cli, "find_flight", lambda *a, **k: FlightKey(2015, 4, 24, "AA", "36", "SAN"))
    with pytest.raises(SystemExit) as e:
        cli.main(["run", "--live"])
    assert e.value.code == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


def test_live_defaults_to_false():
    assert inspect.signature(service.negotiate).parameters["live"].default is False


def test_flight_key_from_spec_round_trip():
    spec = next(iter(DEMO_ROWS.values()))
    month, day = row_date(spec)
    key = FlightKey.from_spec({**spec, "month": month, "day": day})
    assert key == FlightKey(2015, month, day, spec["airline"], spec["flight_number"], spec["origin"])
