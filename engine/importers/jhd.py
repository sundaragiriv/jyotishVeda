"""
Importer: Jagannatha Hora birth-data files (.jhd) -> BirthRecord.

An adapter only. The engine never depends on this format; files are
converted into the platform's own BirthRecord on the way in.

Format, as decoded and verified against JHora 8.0 sample files
(one value per line):

  1  month
  2  day
  3  year
  4  time            H.MM  (hours . minutes; minutes may carry a fraction,
                            17.506667 = 17:50:40)
  5  time zone       H.MM, sign inverted: -5.30 = UTC+05:30
  6  longitude       D.MM, sign inverted: -81.08 = 81°08' East
  7  latitude        D.MM, North positive
  --- short files end here (7-8 lines) ---
  Layout A (modern, 14-18 lines):
  8  unidentified numeric (usually 0)
  9  time zone, decimal hours, sign inverted (-5.5 = UTC+5.5)
  10 time zone, decimal hours (repeat)
  11-12 unidentified
  13 place, 14 country
  15 unidentified, 16 pressure (mbar), 17 temperature (°C), 18 unidentified
  Layout B (legacy, 18 lines):
  8  unidentified numeric
  9-17 cached sidereal longitudes: Surya, Chandra, Mangala, Budha, Guru,
       Shukra, Shani, Rahu (mean), Lagna  (confirmed by recomputation)
  18 9-character flag string, e.g. "000100100" (unidentified)

Verified: time and tz decoding (LMT files match longitude/15 to the
second; cached positions match recomputation with a constant, epoch-
dependent offset, i.e. an older ayanamsha definition, not a time error).
Unverified: sign convention for Western longitudes and Southern
latitudes (all samples are India). Such files import with a warning.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from models.birth import BirthRecord, Place, Provenance, TimeStandard

CACHED_KEYS = ["Surya", "Chandra", "Mangala", "Budha", "Guru",
               "Shukra", "Shani", "Rahu", "Lagna"]
_FLAGS = re.compile(r"^[01]{9}$")
_UNKNOWN_PLACE = {"", "unknown"}


class JhdImportError(ValueError):
    pass


class JhdImport(BaseModel):
    record: BirthRecord
    layout: str                                  # "short" | "A" | "B"
    cached_longitudes: Optional[dict[str, float]] = None   # layout B only
    atmosphere: Optional[dict[str, float]] = None           # pressure/temperature
    unidentified: dict[int, str] = {}            # line no -> raw value


# ---------------------------------------------------------------------------

def _split_hmm(value: float, what: str) -> float:
    """H.MM(fraction) -> decimal units. Rejects minutes >= 60."""
    sign = -1.0 if value < 0 else 1.0
    v = abs(value)
    whole = int(v)
    minutes = round((v - whole) * 100.0, 9)
    if minutes >= 60.0:
        raise JhdImportError(f"{what}={value}: minutes {minutes:.4f} >= 60, not H.MM")
    return sign * (whole + minutes / 60.0)


def _num(lines: list[str], i: int, what: str) -> float:
    try:
        return float(lines[i])
    except (IndexError, ValueError):
        raise JhdImportError(f"line {i + 1} ({what}) missing or not numeric")


def _layout(lines: list[str]) -> str:
    if len(lines) >= 18 and _FLAGS.match(lines[17]):
        return "B"
    if len(lines) >= 14:
        return "A"
    if len(lines) >= 7:
        return "short"
    raise JhdImportError(f"expected at least 7 lines, found {len(lines)}")


def _time_standard(offset_h: float, lon_east: float) -> TimeStandard:
    if abs(offset_h - lon_east / 15.0) * 3600 < 60:
        return TimeStandard.LMT
    if abs(offset_h * 4 - round(offset_h * 4)) * 900 < 1:   # multiple of 15 min
        return TimeStandard.ZONE
    return TimeStandard.UNKNOWN


# ---------------------------------------------------------------------------

def parse_jhd(text: str, name: str, source_file: Optional[str] = None) -> JhdImport:
    lines = [ln.strip() for ln in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    layout = _layout(lines)
    warnings: list[str] = []

    month, day, year = (int(_num(lines, i, w)) for i, w in
                        enumerate(["month", "day", "year"]))
    t_hours = _split_hmm(_num(lines, 3, "time"), "time")
    if not 0 <= t_hours < 24:
        raise JhdImportError(f"time {t_hours} h outside 0-24")
    try:
        midnight = datetime(year, month, day)
    except ValueError as e:
        raise JhdImportError(f"invalid date {year}-{month}-{day}: {e}")
    # 6 stored decimals of H.MM resolve ~0.006 s; keep 0.01 s, no false precision
    local = midnight + timedelta(milliseconds=10 * round(t_hours * 360_000))

    offset_h = -_split_hmm(_num(lines, 4, "timezone"), "timezone")
    lon = -_split_hmm(_num(lines, 5, "longitude"), "longitude")
    lat = _split_hmm(_num(lines, 6, "latitude"), "latitude")

    if lon < 0:
        warnings.append("Western longitude: JHora sign convention for West is unverified")
    if lat < 0:
        warnings.append("Southern latitude: JHora sign convention for South is unverified")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise JhdImportError(f"coordinates out of range: lat {lat}, lon {lon}")

    place_name = country = None
    atmosphere = None
    cached = None
    unidentified: dict[int, str] = {}

    if layout == "A":
        dec_tz = -_num(lines, 8, "timezone (decimal)")
        if abs(dec_tz - offset_h) * 3600 > 1:
            warnings.append(f"timezone fields disagree: line 5 = {offset_h:.6f} h, "
                            f"line 9 = {dec_tz:.6f} h; using line 5")
        place_name = None if lines[12].lower() in _UNKNOWN_PLACE else lines[12]
        country = None if lines[13].lower() in _UNKNOWN_PLACE else lines[13]
        if len(lines) >= 17:
            atmosphere = {"pressure_mbar": _num(lines, 15, "pressure"),
                          "temperature_c": _num(lines, 16, "temperature")}
        for ln in (8, 11, 12, 15, 18):
            if len(lines) >= ln:
                unidentified[ln] = lines[ln - 1]
    elif layout == "B":
        cached = {k: _num(lines, 8 + i, f"cached {k}") for i, k in enumerate(CACHED_KEYS)}
        unidentified = {8: lines[7], 18: lines[17]}
    elif len(lines) >= 8:
        unidentified[8] = lines[7]

    std = _time_standard(offset_h, lon)
    if std is TimeStandard.UNKNOWN:
        warnings.append(f"offset {offset_h:+.4f} h is neither LMT nor a 15-min zone")

    record = BirthRecord(
        name=name,
        local_datetime=local,
        utc_offset_seconds=round(offset_h * 3600),
        time_standard=std,
        place=Place(name=place_name, country=country, latitude=round(lat, 6),
                    longitude=round(lon, 6)),
        provenance=Provenance(source_format="jhora.jhd", source_file=source_file,
                              raw_fields=lines, warnings=warnings),
    )
    return JhdImport(record=record, layout=layout, cached_longitudes=cached,
                     atmosphere=atmosphere, unidentified=unidentified)


def load_jhd(path: str | Path) -> JhdImport:
    p = Path(path)
    return parse_jhd(p.read_text(encoding="latin-1"), name=p.stem, source_file=p.name)
