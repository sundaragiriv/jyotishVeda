"""
Graha Sphuta — sidereal positions of the Navagraha.

Computes the nirayana (sidereal) longitude of the nine grahas for a UTC
moment and maps each to its Rasi, Nakshatra and Pada.

    Surya (Sun), Chandra (Moon), Mangala (Mars), Budha (Mercury),
    Guru (Jupiter), Shukra (Venus), Shani (Saturn), Rahu, Ketu

Conventions (defaults match Jagannatha Hora's defaults):
    * Ayanamsha      : Lahiri (Chitrapaksha), swe.SIDM_LAHIRI
    * Frame          : geocentric, apparent positions
    * Rahu           : Mean node (set node="true" for True/osculating node)
    * Ketu           : Rahu + 180 deg, same speed as Rahu

Geocentric longitudes do not depend on the observer's latitude/longitude.
They are accepted here because the chart needs them (Lagna, bhavas), and
they are used for graha positions only when topocentric=True.

Usage:
    python grahas.py 1990-08-15T04:30:00Z 17.385 78.4867
    python grahas.py 1990-08-15T04:30:00Z 17.385 78.4867 --node true --topocentric
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import swisseph as swe

# ---------------------------------------------------------------------------
# Classical reference tables
# ---------------------------------------------------------------------------

RASIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
]

# Rasi adhipati (sign lords), index-aligned with RASIS
RASI_LORDS = [
    "Mangala", "Shukra", "Budha", "Chandra", "Surya", "Budha",
    "Shukra", "Mangala", "Guru", "Shani", "Shani", "Guru",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

# Vimshottari dasha lords repeat every 9 nakshatras, starting from Ashwini
VIMSHOTTARI_LORDS = [
    "Ketu", "Shukra", "Surya", "Chandra", "Mangala",
    "Rahu", "Guru", "Shani", "Budha",
]

GRAHAS = [
    ("Surya", swe.SUN),
    ("Chandra", swe.MOON),
    ("Mangala", swe.MARS),
    ("Budha", swe.MERCURY),
    ("Guru", swe.JUPITER),
    ("Shukra", swe.VENUS),
    ("Shani", swe.SATURN),
]

RASI_SPAN = 30.0
NAKSHATRA_SPAN = 360.0 / 27.0      # 13 deg 20 min
PADA_SPAN = NAKSHATRA_SPAN / 4.0   # 3 deg 20 min

# Guard against float noise pushing an exact boundary into the previous
# division (e.g. 29.999999999999996 instead of 30.0). ~1e-9 deg is far
# below ephemeris precision.
_EPS = 1e-9

# Use Swiss Ephemeris data files if present, else fall back to the built-in
# Moshier ephemeris. The flag actually used is reported in the output.
_EPHE_PATH = os.environ.get("SE_EPHE_PATH")
if _EPHE_PATH:
    swe.set_ephe_path(_EPHE_PATH)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class GrahaPosition:
    graha: str
    longitude: float          # nirayana longitude, 0-360
    longitude_dms: str
    speed_deg_per_day: float
    retrograde: bool          # vakri
    rasi_index: int           # 1-12
    rasi: str
    rasi_lord: str
    degree_in_rasi: float
    degree_in_rasi_dms: str
    nakshatra_index: int      # 1-27
    nakshatra: str
    nakshatra_lord: str
    pada: int                 # 1-4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(deg: float) -> float:
    deg = deg % 360.0
    return 0.0 if deg >= 360.0 - _EPS else deg


def to_dms(deg: float) -> str:
    """Degrees -> D°M'S.ss" (seconds rounded to 2 dp, with carry)."""
    total = round(abs(deg) * 3600.0, 2)
    d, rem = divmod(total, 3600.0)
    m, s = divmod(rem, 60.0)
    return f"{int(d)}°{int(m):02d}'{s:05.2f}\""


def classify(longitude: float) -> dict:
    """Map a sidereal longitude to Rasi, Nakshatra and Pada."""
    lon = _normalize(longitude)

    rasi_idx = min(int((lon + _EPS) // RASI_SPAN), 11)
    nak_idx = min(int((lon + _EPS) // NAKSHATRA_SPAN), 26)
    within_nak = lon - nak_idx * NAKSHATRA_SPAN
    pada = min(int((within_nak + _EPS) // PADA_SPAN), 3) + 1
    deg_in_rasi = max(lon - rasi_idx * RASI_SPAN, 0.0)

    return {
        "rasi_index": rasi_idx + 1,
        "rasi": RASIS[rasi_idx],
        "rasi_lord": RASI_LORDS[rasi_idx],
        "degree_in_rasi": round(deg_in_rasi, 6),
        "degree_in_rasi_dms": to_dms(deg_in_rasi),
        "nakshatra_index": nak_idx + 1,
        "nakshatra": NAKSHATRAS[nak_idx],
        "nakshatra_lord": VIMSHOTTARI_LORDS[nak_idx % 9],
        "pada": pada,
    }


def _parse_utc(ts: str | datetime) -> datetime:
    if isinstance(ts, datetime):
        dt = ts
    else:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware UTC (e.g. '...Z').")
    return dt.astimezone(timezone.utc)


def _julian_day_ut(dt: datetime) -> float:
    """UTC civil time -> Julian Day (UT1), leap-second aware via swe.utc_to_jd."""
    seconds = dt.second + dt.microsecond / 1e6
    _jd_et, jd_ut = swe.utc_to_jd(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, seconds, swe.GREG_CAL
    )
    return jd_ut


def julian_day_ut(ts: str | datetime) -> float:
    """Public helper: aware UTC timestamp -> Julian Day (UT1)."""
    return _julian_day_ut(_parse_utc(ts))


def jd_to_utc(jd_ut: float) -> datetime:
    """Julian Day (UT) -> aware UTC datetime (to the millisecond)."""
    y, m, d, h, mi, s = swe.jdut1_to_utc(jd_ut, swe.GREG_CAL)
    s = min(s, 59.999)            # inside a leap second: clamp, datetime has no :60
    whole = int(s)
    ms = min(int(round((s - whole) * 1000)), 999)
    return datetime(y, m, d, h, mi, whole, ms * 1000, tzinfo=timezone.utc)


def _ephemeris_name(retflag: int) -> str:
    if retflag & swe.FLG_SWIEPH:
        return "Swiss Ephemeris (data files)"
    if retflag & swe.FLG_JPLEPH:
        return "JPL"
    return "Moshier (built-in analytical)"


# ---------------------------------------------------------------------------
# Main calculation
# ---------------------------------------------------------------------------

def compute_graha_positions(
    utc_timestamp: str | datetime,
    latitude: float,
    longitude: float,
    *,
    altitude_m: float = 0.0,
    node: str = "mean",
    topocentric: bool = False,
    ayanamsha: int = swe.SIDM_LAHIRI,
) -> dict:
    """
    Sidereal positions of the Navagraha for a UTC moment.

    Args:
        utc_timestamp: ISO-8601 string with 'Z' / offset, or aware datetime.
        latitude, longitude: observer, decimal degrees (N+, E+).
        altitude_m: observer altitude, used only when topocentric=True.
        node: "mean" (default) or "true" for Rahu/Ketu.
        topocentric: False (default) = geocentric, the Jyotish convention.
        ayanamsha: a swe.SIDM_* constant, default Lahiri.
    """
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be within [-90, 90]")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be within [-180, 180]")
    if node not in ("mean", "true"):
        raise ValueError("node must be 'mean' or 'true'")

    dt = _parse_utc(utc_timestamp)
    jd_ut = _julian_day_ut(dt)

    swe.set_sid_mode(ayanamsha, 0, 0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    if topocentric:
        swe.set_topo(longitude, latitude, altitude_m)
        flags |= swe.FLG_TOPOCTR

    positions: list[GrahaPosition] = []
    ephemeris_used = None

    def build(name: str, lon: float, speed: float) -> GrahaPosition:
        lon = _normalize(lon)
        return GrahaPosition(
            graha=name,
            longitude=lon,                    # full precision; round only for display
            longitude_dms=to_dms(lon),
            speed_deg_per_day=speed,
            retrograde=speed < 0,
            **classify(lon),
        )

    for name, pid in GRAHAS:
        xx, retflag = swe.calc_ut(jd_ut, pid, flags)
        ephemeris_used = ephemeris_used or _ephemeris_name(retflag)
        positions.append(build(name, xx[0], xx[3]))

    node_id = swe.MEAN_NODE if node == "mean" else swe.TRUE_NODE
    xx, _ = swe.calc_ut(jd_ut, node_id, flags)
    rahu_lon, rahu_speed = xx[0], xx[3]
    positions.append(build("Rahu", rahu_lon, rahu_speed))
    positions.append(build("Ketu", rahu_lon + 180.0, rahu_speed))

    # True ayanamsha (includes nutation in longitude), consistent with the
    # apparent positions above: tropical_apparent - ayanamsha == sidereal.
    # swe.get_ayanamsa_ut() would return the mean value, ~15" different.
    _, ayan_value = swe.get_ayanamsa_ex_ut(jd_ut, swe.FLG_SWIEPH)
    ayan_value = (ayan_value + 180.0) % 360.0 - 180.0   # signed: negative before ~285 CE

    return {
        "input": {
            "utc": dt.isoformat().replace("+00:00", "Z"),
            "latitude": latitude,
            "longitude": longitude,
            "altitude_m": altitude_m,
        },
        "settings": {
            "zodiac": "sidereal",
            "ayanamsha": swe.get_ayanamsa_name(ayanamsha),
            "ayanamsha_value": round(ayan_value, 6),
            "ayanamsha_dms": ("-" if ayan_value < 0 else "") + to_dms(ayan_value),
            "node": node,
            "frame": "topocentric" if topocentric else "geocentric",
            "ephemeris": ephemeris_used,
            "swisseph_version": swe.version,
        },
        "julian_day_ut": round(jd_ut, 8),
        "grahas": [asdict(p) for p in positions],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    p = argparse.ArgumentParser(description="Sidereal Navagraha positions (Lahiri).")
    p.add_argument("utc", help="UTC timestamp, e.g. 1990-08-15T04:30:00Z")
    p.add_argument("lat", type=float, help="latitude, decimal degrees (N+)")
    p.add_argument("lon", type=float, help="longitude, decimal degrees (E+)")
    p.add_argument("--alt", type=float, default=0.0, help="altitude in metres")
    p.add_argument("--node", choices=["mean", "true"], default="mean")
    p.add_argument("--topocentric", action="store_true")
    a = p.parse_args()

    result = compute_graha_positions(
        a.utc, a.lat, a.lon,
        altitude_m=a.alt, node=a.node, topocentric=a.topocentric,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _main()
