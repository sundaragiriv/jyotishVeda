"""
Vimshottari dasha — the 120-year nakshatra dasha (BPHS).

Order and years:
    Ketu 7, Shukra 20, Surya 6, Chandra 10, Mangala 7,
    Rahu 18, Guru 16, Shani 19, Budha 17            (total 120)

The Moon's natal nakshatra gives the starting lord (Ashwini -> Ketu,
Bharani -> Shukra, ... repeating every 9 nakshatras). The portion of that
nakshatra the Moon has already traversed is the portion of the first
mahadasha already elapsed at birth; the rest is the "balance".

Each sub-level divides its parent in the same proportions, starting from
the parent's own lord:  child length = parent length x child years / 120.

Setting (explicit): year_length in days.
    365.2425   mean Gregorian year (default)
    365.25     Julian year
    365.256363 sidereal year
    360        savana (civil) year
Different software defaults differ here; dates shift by days over decades.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from astro_core.grahas import NAKSHATRAS

LORDS = ["Ketu", "Shukra", "Surya", "Chandra", "Mangala",
         "Rahu", "Guru", "Shani", "Budha"]
YEARS = dict(zip(LORDS, [7, 20, 6, 10, 7, 18, 16, 19, 17]))
TOTAL = 120
NAK_SPAN = 360.0 / 27.0
LEVEL_NAMES = ["mahadasha", "antardasha", "pratyantardasha",
               "sookshmadasha", "pranadasha"]
YEAR_LENGTHS = {"gregorian": 365.2425, "julian": 365.25,
                "sidereal": 365.256363, "savana": 360.0}


def _sequence_from(lord: str) -> list[str]:
    i = LORDS.index(lord)
    return LORDS[i:] + LORDS[:i]


def _build(lord: str, start: datetime, years: float, level: int, depth: int,
           ydays: float) -> dict:
    end = start + timedelta(days=years * ydays)
    node = {"lord": lord, "level": LEVEL_NAMES[level],
            "start": start.isoformat(), "end": end.isoformat(),
            "years": round(years, 6)}
    if level + 1 < depth:
        children, t = [], start
        for sub in _sequence_from(lord):
            sub_years = years * YEARS[sub] / TOTAL
            children.append(_build(sub, t, sub_years, level + 1, depth, ydays))
            t += timedelta(days=sub_years * ydays)
        node["periods"] = children
    return node


def compute_vimshottari(
    moon_longitude: float,
    birth_utc: datetime,
    *,
    depth: int = 3,
    year_length: str | float = "gregorian",
    cycles: int = 1,
) -> dict:
    """
    moon_longitude: sidereal longitude of Chandra (degrees).
    birth_utc: aware UTC datetime.
    depth: 1 = mahadashas only ... 5 = down to prana.
    cycles: how many 120-year cycles to list (1 covers any lifespan).
    """
    if birth_utc.tzinfo is None:
        raise ValueError("birth_utc must be timezone-aware")
    if not 1 <= depth <= 5:
        raise ValueError("depth must be 1-5")
    ydays = YEAR_LENGTHS[year_length] if isinstance(year_length, str) else float(year_length)

    lon = moon_longitude % 360.0
    nak = min(int(lon // NAK_SPAN), 26)
    first = LORDS[nak % 9]
    elapsed = (lon - nak * NAK_SPAN) / NAK_SPAN
    balance_years = YEARS[first] * (1 - elapsed)

    # The first mahadasha "started" before birth; its full span is listed
    # so sub-periods before birth are visible and consistent.
    t = birth_utc - timedelta(days=YEARS[first] * elapsed * ydays)
    periods = []
    for c in range(cycles):
        for lord in _sequence_from(first):
            periods.append(_build(lord, t, YEARS[lord], 0, depth, ydays))
            t += timedelta(days=YEARS[lord] * ydays)

    return {
        "system": "vimshottari",
        "settings": {"year_length_days": ydays, "depth": depth},
        "moon_nakshatra": NAKSHATRAS[nak],
        "starting_lord": first,
        "elapsed_fraction": round(elapsed, 8),
        "balance_at_birth": {"lord": first, "years": round(balance_years, 6),
                             "days": round(balance_years * ydays, 2)},
        "periods": periods,
    }


def active_periods(dasha: dict, at: datetime) -> list[dict]:
    """Chain of periods (maha -> deepest level) running at a given moment."""
    chain: list[dict] = []
    nodes: Optional[list[dict]] = dasha["periods"]
    if at.tzinfo is None:
        raise ValueError("at must be timezone-aware")
    parse = datetime.fromisoformat
    while nodes:
        hit = next((n for n in nodes if parse(n["start"]) <= at < parse(n["end"])), None)
        if hit is None:
            break
        chain.append({k: hit[k] for k in ("lord", "level", "start", "end")})
        nodes = hit.get("periods")
    return chain
