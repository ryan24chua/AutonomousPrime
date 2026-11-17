"""One world per negotiation: `build_world(day_rows, focal_row, seed)` returns a frozen `WorldState`.

The state is built once per `negotiate()`, from the loader's rows (`infra.data`, outcome columns already
removed). Each role reads only its own view:
  * atc     - `World`: background arrivals (real + synthetic filler), weather window, the focal's earliest arrival.
  * pilot   - `PilotInputs`: schedule, alternate, crew report, onward connections.
  * ground  - `GroundState`: gates and their occupancy, crew shift, connecting pax, the next departure.
The checker, the cost and the fallback are code, not parties: they read the whole state.

Every synthetic or derived value carries a label (`real`, `derived`, `workbook`, `synthetic`); `WorldState.provenance`
collects them. Every view uses the same rules for the disrupted arrival, the event, the date, "2400" and the
seeding (`flight_rng`).
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from autonomousprime.agents.atc import config as atc_config
from autonomousprime.agents.constraints import ASSUMPTIONS, AirportLimits, airport_limits, fuel_crew_rules
from autonomousprime.agents.ground.assumptions import LIMITS_SOURCE
from autonomousprime.core.timeutil import dot_to_hhmm, hhmm_to_min, to_min
from autonomousprime.infra.data import airports


# ---------------------------------------------------------------- ATC view
@dataclass
class Arrival:
    flight_id: str
    airline: str
    tail: str
    sched_min: int  # scheduled arrival, minutes after local midnight
    wake: str
    provenance: str  # "real" or "synthetic"


@dataclass
class World:
    """The ATC view."""

    date: str
    dest: str
    focal: dict  # focal row with hindsight columns removed
    event: dict  # {"type": "weather"|"late_aircraft", "magnitude_min": int}
    focal_earliest_arr_min: int  # scheduled arrival, pushed by late-aircraft delay
    weather_hours: list[int]
    background: list[Arrival]
    weather_cut: float = atc_config.WEATHER_CUT
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- Pilot view
@dataclass(frozen=True)
class Alternate:
    iata: str
    name: str
    distance_nm: float
    provenance: str = "real coordinates (airports.csv), nearest airport > 100 nm rule"


@dataclass(frozen=True)
class Connection:
    flight: str  # e.g. "DL1452"
    to: str  # onward destination
    sched_dep: str  # HH:MM, destination-local
    pax: int  # connecting passengers from the focal flight
    last_of_day: bool  # no later same-airline departure to that city in the data
    provenance: str = "real onward flight (flights.csv); pax count synthetic (seeded)"


@dataclass(frozen=True)
class PilotInputs:
    """The Pilot view."""

    flight: str
    tail: str
    origin: str
    dest: str
    date: str  # YYYY-MM-DD
    sched_dep: str  # HH:MM origin-local
    sched_arr: str  # HH:MM dest-local
    sched_time_min: int
    distance_mi: int
    aircraft_class: str  # "narrowbody" | "widebody" (assumption by distance)
    event_type: str  # "weather" | "late_aircraft"
    event_magnitude_min: int  # WEATHER_DELAY or LATE_AIRCRAFT_DELAY (reported cause minutes)
    airborne: bool  # default False (pre-departure)
    alternate: Alternate
    crew_report: str  # HH:MM origin-local (derived, approximate)
    mct_min: float
    connections: tuple[Connection, ...] = field(default_factory=tuple)
    seed: int = 0


# ---------------------------------------------------------------- Ground view
@dataclass(frozen=True)
class BusyWindow:
    start: int  # minutes from midnight
    end: int
    label: str


@dataclass
class GroundState:
    """The Ground view."""

    seed: int
    airport: str
    limits: AirportLimits  # from the workbook (agents.constraints)
    focal_flight: str
    tail: str
    event_type: str  # "weather" | "late_aircraft"
    event_magnitude_min: int
    scheduled_arrival_min: int
    disrupted_arrival_min: int  # earliest arrival, the same for every view (earliest_arrival_min)
    event_end_min: int  # scheduled arrival + reported delay: the given disruption (register S5)
    scheduled_gate: str
    now_min: int  # when the disruption was announced to Ground
    next_departure_min: int  # focal aircraft's next scheduled departure
    crew_shift_start_min: int
    connecting_pax: int
    connection_slack_min: int
    crew_shift_min: int  # workbook: ground crew shift length
    gate_change_notice_min: int  # workbook: minimum notice before arrival
    gate_busy: dict[str, list[BusyWindow]]
    provenance: dict[str, str] = field(default_factory=dict)

    @property
    def crew_shift_end_min(self) -> int:
        """Ground crew shift end = start + the workbook's shift length (minutes from midnight)."""
        return self.crew_shift_start_min + self.crew_shift_min


# ---------------------------------------------------------------- the world
ROLES = ("atc", "pilot", "ground")


@dataclass(frozen=True)
class WorldState:
    """One disruption, built once per negotiation. Roles read `view(role)`; code may read everything."""

    seed: int
    focal: dict  # the focal row, hindsight columns removed
    atc: World
    pilot: PilotInputs
    ground: GroundState

    @property
    def negotiation_id(self) -> str:
        f = self.focal
        return f"{f['DESTINATION_AIRPORT']}-{self.atc.date.replace('-', '')}-{f['AIRLINE']}{f['FLIGHT_NUMBER']}"

    def view(self, role: str) -> World | PilotInputs | GroundState:
        if role not in ROLES:
            raise KeyError(f"unknown role {role!r}")
        return getattr(self, role)

    @property
    def provenance(self) -> dict[str, str]:
        """Every label the three views carry, one entry per input."""
        out = {
            "atc: focal row, background arrivals, weather window": "real (DOT 2015)",
            "atc: filler arrivals": "synthetic: " + "; ".join(self.atc.notes),
            "atc: wake class": f"synthetic default {atc_config.DEFAULT_WAKE_CLASS}",
            "pilot: schedule, event": "real (DOT 2015)",
            "pilot: alternate": self.pilot.alternate.provenance,
            "pilot: crew report": "derived (first scheduled leg of the tail minus the workbook report time)",
            "pilot: connections": Connection.provenance,
        }
        out.update({f"ground: {k}": v for k, v in self.ground.provenance.items()})
        return out


def build_world(
    day_rows: list[dict], focal_row: dict, seed: int = 7, weather_cut: float = atc_config.WEATHER_CUT
) -> WorldState:
    """The world for one disrupted arrival. `day_rows` are every loader row of the focal's date (file order) and
    `focal_row` is one of them (the same object). Raises ValueError if a row is from another date."""
    _check_one_date(day_rows, focal_row)
    return WorldState(
        seed=seed,
        focal=strip_hindsight(focal_row),
        atc=_atc_view(day_rows, focal_row, seed, weather_cut),
        pilot=_pilot_view(day_rows, focal_row, seed),
        ground=_ground_view(day_rows, focal_row, seed),
    )


# ---------------------------------------------------------------- shared row helpers
def date_of(row: dict) -> tuple[str, str, str]:
    """The full date of a row (YEAR, MONTH, DAY), as the exact csv strings."""
    return row["YEAR"], row["MONTH"], row["DAY"]


def flight_rng(seed: int, row: dict, view: str) -> random.Random:
    """The one seeding rule: every synthetic draw for a view of a flight comes from the run seed, the flight's
    full date, airline, number and origin, and the view's name. Two flights never share draws; the same
    flight, seed and view always get the same ones."""
    key = f"{seed}-{'-'.join(date_of(row))}-{row['AIRLINE']}{row['FLIGHT_NUMBER']}-{row['ORIGIN_AIRPORT']}-{view}"
    return random.Random(key)


def _check_one_date(day_rows: list[dict], focal_row: dict) -> None:
    """The one year filter: a world is built from the rows of the focal's full date only."""
    date = date_of(focal_row)
    other = next((r for r in day_rows if date_of(r) != date), None)
    if other is not None:
        raise ValueError(f"world for {'-'.join(date)} got a row dated {'-'.join(date_of(other))}")


def _num(v: str) -> float:
    return float(v) if v not in ("", None) else 0.0


def event_of(row: dict) -> dict | None:
    """The disruption on a row, the one classifier for every view: weather if WEATHER_DELAY > 15 min,
    else late aircraft if LATE_AIRCRAFT_DELAY > 20 min, else none. The size is the recorded cause minutes,
    known at decision time (register S5)."""
    if _num(row["WEATHER_DELAY"]) > 15:
        return {"type": "weather", "magnitude_min": int(_num(row["WEATHER_DELAY"]))}
    if _num(row["LATE_AIRCRAFT_DELAY"]) > 20:
        return {"type": "late_aircraft", "magnitude_min": int(_num(row["LATE_AIRCRAFT_DELAY"]))}
    return None


def earliest_arrival_min(sched_min: int, event: dict) -> int:
    """The earliest the focal can arrive, known at decision time (one rule for every view).
    A late inbound aircraft pushes the scheduled arrival by its reported delay; weather does not move the
    aircraft, it cuts the airport's capacity, and ATC's arrival menu decides how late the slot is."""
    return sched_min + (event["magnitude_min"] if event["type"] == "late_aircraft" else 0)


def strip_hindsight(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in atc_config.HINDSIGHT_COLUMNS}


def weather_hours(day_rows: list[dict], dest: str) -> list[int]:
    counts = Counter(
        hhmm_to_min(r["SCHEDULED_ARRIVAL"]) // 60
        for r in day_rows
        if r["DESTINATION_AIRPORT"] == dest and _num(r["WEATHER_DELAY"]) > 15
    )
    return sorted(h for h, n in counts.items() if n >= atc_config.WEATHER_WINDOW_MIN_DELAYED)


def pick_focal(day_rows: list[dict], dest: str, flight: str | None = None) -> dict:
    """Default focal: the weather-delayed arrival with the largest WEATHER_DELAY in the busiest weather hour."""
    arrivals = [r for r in day_rows if r["DESTINATION_AIRPORT"] == dest and event_of(r)]
    if flight:
        return next(r for r in arrivals if f"{r['AIRLINE']}{r['FLIGHT_NUMBER']}" == flight)
    wx = weather_hours(day_rows, dest)
    busiest = max(wx, key=lambda h: sum(1 for r in arrivals if hhmm_to_min(r["SCHEDULED_ARRIVAL"]) // 60 == h))
    in_hour = [
        r for r in arrivals if hhmm_to_min(r["SCHEDULED_ARRIVAL"]) // 60 == busiest and _num(r["WEATHER_DELAY"]) > 15
    ]
    return max(in_hour, key=lambda r: _num(r["WEATHER_DELAY"]))


# ---------------------------------------------------------------- ATC view builder
def _atc_view(day_rows: list[dict], focal_row: dict, seed: int, weather_cut: float) -> World:
    dest = focal_row["DESTINATION_AIRPORT"]
    event = event_of(focal_row)
    sched = hhmm_to_min(focal_row["SCHEDULED_ARRIVAL"])
    earliest = earliest_arrival_min(sched, event)
    hours = range(sched // 60 - atc_config.HORIZON_HOURS, sched // 60 + atc_config.HORIZON_HOURS + 2)

    background: list[Arrival] = []
    real_per_hour: Counter = Counter()
    for r in day_rows:
        if r is focal_row or r["DESTINATION_AIRPORT"] != dest:
            continue
        m = hhmm_to_min(r["SCHEDULED_ARRIVAL"])
        if m // 60 in hours:
            real_per_hour[m // 60] += 1
            background.append(
                Arrival(
                    f"{r['AIRLINE']}{r['FLIGHT_NUMBER']}",
                    r["AIRLINE"],
                    r["TAIL_NUMBER"],
                    m,
                    atc_config.wake_class(r["TAIL_NUMBER"], r["AIRLINE"]),
                    "real",
                )
            )

    rng = flight_rng(seed, focal_row, "atc")
    for h in hours:
        n_fill = round(real_per_hour[h] * (atc_config.FILLER_DEMAND_MULTIPLIER - 1))
        for i in range(n_fill):
            background.append(
                Arrival(
                    f"SYN{h:02d}{i:02d}",
                    "SYN",
                    "",
                    h * 60 + rng.randrange(60),
                    atc_config.DEFAULT_WAKE_CLASS,
                    "synthetic",
                )
            )
    background.sort(key=lambda a: a.sched_min)

    return World(
        date=f"{focal_row['YEAR']}-{int(focal_row['MONTH']):02d}-{int(focal_row['DAY']):02d}",
        dest=dest,
        focal=strip_hindsight(focal_row),
        event=event,
        focal_earliest_arr_min=earliest,
        weather_hours=weather_hours(day_rows, dest),
        background=background,
        weather_cut=weather_cut,
        notes=[f"filler multiplier {atc_config.FILLER_DEMAND_MULTIPLIER:.2f}x real arrivals per hour (synthetic)"],
    )


# ---------------------------------------------------------------- Pilot view builder
# Columns the Pilot may see. Outcome columns are deliberately absent ("no hindsight").
PILOT_COLUMNS = (
    "YEAR",
    "MONTH",
    "DAY",
    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE",
    "SCHEDULED_ARRIVAL",
    "SCHEDULED_TIME",
    "DISTANCE",
    "WEATHER_DELAY",
    "LATE_AIRCRAFT_DELAY",
)


def haversine_nm(lat1, lon1, lat2, lon2) -> float:
    r_nm = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r_nm * math.asin(math.sqrt(a))


def nearest_alternate(dest: str, min_nm: float = 100.0) -> Alternate:
    aps = airports()
    d = aps[dest]
    lat, lon = float(d["LATITUDE"]), float(d["LONGITUDE"])
    best = None
    for code, a in aps.items():
        if code == dest or not a["LATITUDE"]:
            continue
        dist = haversine_nm(lat, lon, float(a["LATITUDE"]), float(a["LONGITUDE"]))
        if dist > min_nm and (best is None or dist < best[0]):
            best = (dist, code, a["AIRPORT"])
    return Alternate(iata=best[1], name=best[2], distance_nm=round(best[0], 1))


def _schedule_index(day_rows: list[dict]) -> dict:
    """Schedule-only rows of the date, indexed by (month, day, origin), file order."""
    by_origin_day = defaultdict(list)
    for r in day_rows:
        row = {k: r[k] for k in PILOT_COLUMNS}
        by_origin_day[(row["MONTH"], row["DAY"], row["ORIGIN_AIRPORT"])].append(row)
    return by_origin_day


def crew_report_time(row: dict, by_origin_day) -> str:
    """Earliest scheduled departure of this tail that day (from the data) minus 60 min.
    Approximate: flights.csv contains only delayed legs, so the true first leg may be earlier."""
    tail, mo, dy = row["TAIL_NUMBER"], row["MONTH"], row["DAY"]
    first = min(
        to_min(dot_to_hhmm(r["SCHEDULED_DEPARTURE"]))
        for (m, d, _), legs in by_origin_day.items()
        if m == mo and d == dy
        for r in legs
        if r["TAIL_NUMBER"] == tail
    )
    rep = max(first - int(ASSUMPTIONS["crew_report_before_first_leg_min"]), 0)
    return f"{rep // 60:02d}:{rep % 60:02d}"


def derive_connections(row: dict, by_origin_day, rng: random.Random) -> tuple[Connection, ...]:
    """Same-airline departures from the destination 35-180 min after scheduled arrival (real flights),
    with a seeded connecting-passenger count. Undercounts: only delayed flights are in the data."""
    lo, hi = ASSUMPTIONS["connection_window_min"]
    arr = to_min(dot_to_hhmm(row["SCHEDULED_ARRIVAL"]))
    departures = by_origin_day.get((row["MONTH"], row["DAY"], row["DESTINATION_AIRPORT"]), [])
    same_airline = [r for r in departures if r["AIRLINE"] == row["AIRLINE"]]
    out = []
    for r in sorted(same_airline, key=lambda r: r["SCHEDULED_DEPARTURE"]):
        dep = to_min(dot_to_hhmm(r["SCHEDULED_DEPARTURE"]))
        if lo <= dep - arr <= hi:
            later = any(
                x["DESTINATION_AIRPORT"] == r["DESTINATION_AIRPORT"]
                and to_min(dot_to_hhmm(x["SCHEDULED_DEPARTURE"])) > dep
                for x in same_airline
            )
            out.append(
                Connection(
                    flight=f"{r['AIRLINE']}{r['FLIGHT_NUMBER']}",
                    to=r["DESTINATION_AIRPORT"],
                    sched_dep=dot_to_hhmm(r["SCHEDULED_DEPARTURE"]),
                    pax=rng.randint(*ASSUMPTIONS["connection_pax_range"]),
                    last_of_day=not later,
                )
            )
    return tuple(out)


def _pilot_view(day_rows: list[dict], focal_row: dict, seed: int, airborne: bool = False) -> PilotInputs:
    by_origin_day = _schedule_index(day_rows)
    row = {k: focal_row[k] for k in PILOT_COLUMNS}
    event = event_of(row)
    dist = int(float(row["DISTANCE"]))
    limits = airport_limits().get(row["DESTINATION_AIRPORT"])
    mct = ASSUMPTIONS["mct_min"].get(limits.size_class if limits else "", ASSUMPTIONS["mct_min"]["default"])
    return PilotInputs(
        flight=f"{row['AIRLINE']}{row['FLIGHT_NUMBER']}",
        tail=row["TAIL_NUMBER"],
        origin=row["ORIGIN_AIRPORT"],
        dest=row["DESTINATION_AIRPORT"],
        date=f"{row['YEAR']}-{int(row['MONTH']):02d}-{int(row['DAY']):02d}",
        sched_dep=dot_to_hhmm(row["SCHEDULED_DEPARTURE"]),
        sched_arr=dot_to_hhmm(row["SCHEDULED_ARRIVAL"]),
        sched_time_min=int(float(row["SCHEDULED_TIME"])),
        distance_mi=dist,
        aircraft_class="widebody" if dist >= ASSUMPTIONS["widebody_if_distance_mi_at_least"] else "narrowbody",
        event_type=event["type"],
        event_magnitude_min=event["magnitude_min"],
        airborne=airborne,
        alternate=nearest_alternate(row["DESTINATION_AIRPORT"]),
        crew_report=crew_report_time(row, by_origin_day),
        mct_min=mct,
        connections=derive_connections(row, by_origin_day, flight_rng(seed, focal_row, "pilot")),
        seed=seed,
    )


# ---------------------------------------------------------------- Ground view builder
# Columns Ground may see. Outcome columns (DEPARTURE_TIME, ARRIVAL_TIME, ARRIVAL_DELAY, ...) are never read.
GROUND_COLUMNS = (
    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "MONTH",
    "DAY",
    "SCHEDULED_DEPARTURE",
    "SCHEDULED_ARRIVAL",
    "SCHEDULED_TIME",
    "WEATHER_DELAY",
    "LATE_AIRCRAFT_DELAY",
)


def terminal_of(gate: str) -> str:
    """Terminal letter of a gate id such as "C14"."""
    return gate[0]


def _gate_ids(n: int) -> list[str]:
    """Gate ids for an airport: 30 gates per terminal A.. (SYNTHETIC layout)."""
    return [f"{'ABCDEFGH'[i // 30]}{i % 30 + 1}" for i in range(n)]


def _ground_view(day_rows: list[dict], focal_row: dict, seed: int) -> GroundState:
    rows = [{k: r[k] for k in GROUND_COLUMNS} for r in day_rows]
    airline, flight_number, origin = focal_row["AIRLINE"], focal_row["FLIGHT_NUMBER"], focal_row["ORIGIN_AIRPORT"]
    focal = next(
        (
            r
            for r in rows
            if r["AIRLINE"] == airline and r["FLIGHT_NUMBER"] == flight_number and r["ORIGIN_AIRPORT"] == origin
        ),
        None,
    )
    if focal is None:
        raise LookupError("focal flight not found in flights.csv")
    event = event_of(focal)
    if event is None:
        raise LookupError("row is not a weather/late-aircraft disruption")
    event_type, magnitude = event["type"], event["magnitude_min"]

    airport = focal["DESTINATION_AIRPORT"]
    limits = airport_limits()[airport]
    rules = fuel_crew_rules()
    shift_min = round(rules.ground_crew_shift_h * 60)
    notice_min = round(rules.gate_change_notice_min)
    sched_arr = hhmm_to_min(focal["SCHEDULED_ARRIVAL"])
    disrupted_arr = earliest_arrival_min(sched_arr, event)
    # The synthetic gate occupancy and crew shift are anchored on when the event clears: the scheduled
    # arrival plus the reported delay minutes (the airport is backed up until then).
    event_end = sched_arr + magnitude
    rng = flight_rng(seed, focal_row, "ground")

    nxt = [
        hhmm_to_min(r["SCHEDULED_DEPARTURE"])
        for r in rows
        if r["TAIL_NUMBER"] == focal["TAIL_NUMBER"]
        and r["ORIGIN_AIRPORT"] == airport
        and hhmm_to_min(r["SCHEDULED_DEPARTURE"]) > sched_arr
    ]
    if nxt:
        next_dep, next_src = min(nxt), "real (DOT 2015, same tail departing this airport later)"
    else:
        next_dep, next_src = sched_arr + 75, "synthetic (no linked next leg in the filtered data)"

    gates = _gate_ids(limits.gates)
    scheduled_gate = "A12"
    spares = rng.sample(
        [g for g in gates if terminal_of(g) != terminal_of(scheduled_gate)], limits.spare_gates_at_any_time
    )
    busy: dict[str, list[BusyWindow]] = {g: [] for g in gates}
    for g in gates:
        if g == scheduled_gate or g in spares:
            continue
        busy[g].append(BusyWindow(sched_arr - rng.randint(0, 60), event_end + rng.randint(30, 180), "background"))
    # The next flight planned for the focal's gate is itself held, so the gate frees late.
    busy[scheduled_gate].append(
        BusyWindow(sched_arr + 40, event_end + rng.randint(15, 28), "background (next flight at scheduled gate)")
    )

    return GroundState(
        seed=seed,
        airport=airport,
        limits=limits,
        focal_flight=f"{airline}{flight_number}",
        tail=focal["TAIL_NUMBER"],
        event_type=event_type,
        event_magnitude_min=magnitude,
        scheduled_arrival_min=sched_arr,
        disrupted_arrival_min=disrupted_arr,
        event_end_min=event_end,
        scheduled_gate=scheduled_gate,
        now_min=disrupted_arr - 60,
        next_departure_min=next_dep,
        crew_shift_start_min=event_end + rng.randint(10, 30) - shift_min,
        connecting_pax=rng.randint(18, 40),
        connection_slack_min=rng.randint(8, 20),
        crew_shift_min=shift_min,
        gate_change_notice_min=notice_min,
        gate_busy=busy,
        provenance={
            "flight, tail, scheduled times, event type/magnitude": "real (DOT 2015)",
            "disrupted arrival": "derived (earliest arrival: scheduled + late-aircraft delay; weather: scheduled)",
            "announce time": "synthetic (60 min before the disrupted arrival)",
            "next departure": next_src,
            "gate count, min turnaround, spare gates, crew shift, gate-change notice": LIMITS_SOURCE,
            "gate occupancy, scheduled gate, crew shift start, connections": f"synthetic (seed {seed}, keyed per flight), "
            "anchored on scheduled arrival + reported delay",
        },
    )
