"""Time helpers for the core: minutes after local midnight, DOT-style HHMM, display "HH:MM".

Every world builder converts times through this module.
"""


def hhmm_to_min(s: str) -> int:
    """'HH:MM' or DOT-style 'HHMM' (including '2400') -> minutes after midnight (0..1440).
    Raises ValueError if `s` is not a valid time."""
    s = str(s).strip().replace(":", "")
    if not s.isdigit() or len(s) > 4:
        raise ValueError(f"bad time {s!r}")
    s = s.zfill(4)
    h, m = int(s[:2]), int(s[2:])
    if m > 59 or h > 24:
        raise ValueError(f"bad time {s!r}")
    return h * 60 + m


def min_to_hhmm(m: int) -> str:
    """Minutes after midnight -> 'HH:MM', wrapping past midnight."""
    m %= 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def dot_to_hhmm(s: str) -> str:
    """DOT 'HHMM' -> 'HH:MM' for the Pilot's view. '2400' becomes '00:00' of the same date
    (the Pilot's rule today; the ATC and Ground views read '2400' as 1440)."""
    s = s.zfill(4)
    return f"{int(s[:2]) % 24:02d}:{s[2:]}"


def to_min(t: str) -> int:
    """'HH:MM' -> minutes after midnight, without validation (the Pilot's arithmetic)."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)
