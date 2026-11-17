"""Ground's own rules about gates: walking time between gates for connecting passengers (SYNTHETIC).

The Ground view of the world (`GroundState`) is built by `autonomousprime.core.world`.
"""

from autonomousprime.agents.ground.assumptions import WALK_OTHER_TERMINAL_MIN, WALK_SAME_TERMINAL_MIN
from autonomousprime.core.world import terminal_of


# Walking minutes for connecting passengers between two gates (SYNTHETIC rule).
# Args: a, b - gate ids.
# Returns: 0 if same gate, else the same/other-terminal walk time.
def walk_min(a: str, b: str) -> int:
    if a == b:
        return 0
    return WALK_SAME_TERMINAL_MIN if terminal_of(a) == terminal_of(b) else WALK_OTHER_TERMINAL_MIN
