"""
Lagna (ascendant) and Bhavas (houses).

Parashari practice reads the rasi chart with whole-sign houses: the rasi
holding the Lagna is the 1st bhava, the next rasi the 2nd, and so on.
That is the default here. Bhava cusps from a quadrant system are optional
and returned separately, never mixed into the rasi chart.

    house_system="W"  whole sign (default; Parashari rasi chart)
    house_system="S"  Sripati: returns bhava sandhi (starts) and bhava
                      madhya (mid-points = Porphyry cusps, Lagna = 1st madhya)
    any other Swiss Ephemeris code ("P" Placidus, "K" Koch, "E" equal, ...)
                      returns that system's cusps as house starts
"""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from astro_core.grahas import classify, julian_day_ut, to_dms

# Swiss Ephemeris silently falls back to Placidus for unknown codes, so only
# these are accepted.
HOUSE_SYSTEMS = {
    "W": "Whole sign", "S": "Sripati", "P": "Placidus", "K": "Koch",
    "O": "Porphyry", "R": "Regiomontanus", "C": "Campanus", "E": "Equal",
    "B": "Alcabitius",
}


def _houses(jd_ut: float, lat: float, lon: float, hsys: str, ayanamsha: int):
    swe.set_sid_mode(ayanamsha, 0, 0)
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys.encode(), swe.FLG_SIDEREAL)
    return list(cusps)[:12], ascmc


def compute_lagna(
    utc_timestamp: str | datetime,
    latitude: float,
    longitude: float,
    *,
    house_system: str = "W",
    ayanamsha: int = swe.SIDM_LAHIRI,
) -> dict:
    if house_system not in HOUSE_SYSTEMS:
        raise ValueError(f"house_system must be one of {sorted(HOUSE_SYSTEMS)}")
    jd = julian_day_ut(utc_timestamp)
    _, ascmc = _houses(jd, latitude, longitude, "W", ayanamsha)
    asc = ascmc[0] % 360.0
    mc = ascmc[1] % 360.0

    out = {
        "lagna": {"longitude": asc, "longitude_dms": to_dms(asc), **classify(asc)},
        "mc": {"longitude": mc, "longitude_dms": to_dms(mc), **classify(mc)},
        "house_system": house_system,
    }

    if house_system == "W":
        return out
    if house_system == "S":
        starts, _ = _houses(jd, latitude, longitude, "S", ayanamsha)
        madhya, _ = _houses(jd, latitude, longitude, "O", ayanamsha)
        out["bhava_sandhi"] = [round(c % 360, 6) for c in starts]
        out["bhava_madhya"] = [round(c % 360, 6) for c in madhya]
    else:
        starts, _ = _houses(jd, latitude, longitude, house_system, ayanamsha)
        out["bhava_start"] = [round(c % 360, 6) for c in starts]
    return out


def whole_sign_house(lagna_rasi_index: int, rasi_index: int) -> int:
    """1-based bhava of a body in whole-sign houses (both indices 1-12)."""
    return (rasi_index - lagna_rasi_index) % 12 + 1


def bhava_of(longitude: float, starts: list[float]) -> int:
    """1-based house for a longitude given 12 house-start cusps."""
    lon = longitude % 360.0
    for i in range(12):
        a, b = starts[i], starts[(i + 1) % 12]
        span = (b - a) % 360.0
        if (lon - a) % 360.0 < span:
            return i + 1
    return 12
