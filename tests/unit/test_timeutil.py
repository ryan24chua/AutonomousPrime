"""core.timeutil: one rule for DOT times, "2400" included."""

import pytest

from autonomousprime.core.timeutil import dot_to_hhmm, hhmm_to_min, min_to_hhmm, to_min


@pytest.mark.parametrize("dot, minutes", [("0005", 5), ("5", 5), ("1734", 1054), ("2359", 1439), ("2400", 1440)])
def test_one_rule_for_dot_times(dot, minutes):
    assert hhmm_to_min(dot) == minutes
    assert to_min(dot_to_hhmm(dot)) == minutes  # the Pilot's view agrees with ATC and Ground


def test_2400_is_end_of_day_not_midnight():
    assert dot_to_hhmm("2400") == "24:00"
    assert min_to_hhmm(1440) == "00:00"  # display wraps; arithmetic uses minutes


@pytest.mark.parametrize("bad", ["2460", "2500", "12345", "ab", ""])
def test_bad_times_raise(bad):
    with pytest.raises(ValueError):
        hhmm_to_min(bad)
