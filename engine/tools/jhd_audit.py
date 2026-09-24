"""
Audit a folder of JHora .jhd files: import each one, report what was
decoded, and where a file carries JHora-computed longitudes (layout B),
compare them with our engine.

    python -m tools.jhd_audit <folder-or-files...> [--json out.json]

The comparison splits each difference into:
  offset   - the median difference across all bodies (a constant shift
             means a different ayanamsha definition, not a data error)
  residual - what remains per body after removing that offset
             (a real disagreement in time, place or ephemeris)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import swisseph as swe

from astro_core.grahas import compute_graha_positions
from importers.jhd import JhdImport, JhdImportError, load_jhd


def _wrap(d: float) -> float:
    return (d + 180.0) % 360.0 - 180.0


def _lagna(jd_ut: float, lat: float, lon: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    _, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W", swe.FLG_SIDEREAL)
    return ascmc[0]


def crosscheck(imp: JhdImport) -> dict | None:
    if not imp.cached_longitudes:
        return None
    r = imp.record
    res = compute_graha_positions(r.utc_datetime, r.place.latitude, r.place.longitude)
    ours = {g["graha"]: g["longitude"] for g in res["grahas"]}
    ours["Lagna"] = _lagna(res["julian_day_ut"], r.place.latitude, r.place.longitude)
    diffs = {k: _wrap(v - ours[k]) * 3600 for k, v in imp.cached_longitudes.items()}
    offset = statistics.median(diffs.values())
    return {
        "offset_arcsec": round(offset, 1),
        "residual_arcsec": {k: round(d - offset, 1) for k, d in diffs.items()},
        "max_residual_arcsec": round(max(abs(d - offset) for d in diffs.values()), 1),
    }


def audit(paths: list[Path]) -> list[dict]:
    files = [f for p in paths for f in (sorted(p.glob("*.jhd")) if p.is_dir() else [p])]
    out = []
    for f in files:
        try:
            imp = load_jhd(f)
        except JhdImportError as e:
            out.append({"file": f.name, "error": str(e)})
            continue
        r = imp.record
        out.append({
            "file": f.name,
            "layout": imp.layout,
            "local": r.local_datetime.isoformat(),
            "utc": r.utc_datetime.isoformat(),
            "offset_h": round(r.utc_offset_seconds / 3600, 4),
            "time_standard": r.time_standard.value,
            "lat": r.place.latitude,
            "lon": r.place.longitude,
            "place": r.place.name,
            "warnings": r.provenance.warnings if r.provenance else [],
            "crosscheck": crosscheck(imp),
        })
    return out


def _main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    rows = audit(a.paths)

    for row in rows:
        if "error" in row:
            print(f"ERROR {row['file']}: {row['error']}")
            continue
        cc = row["crosscheck"]
        cc_txt = (f"  offset {cc['offset_arcsec']:+.1f}\"  max residual "
                  f"{cc['max_residual_arcsec']:.1f}\"") if cc else ""
        print(f"{row['file'][:34]:34} {row['layout']:5} {row['utc'][:19]}  "
              f"{row['time_standard']:4} {row['lat']:8.4f} {row['lon']:9.4f}{cc_txt}")
        for w in row["warnings"]:
            print(f"    ! {w}")
    if a.json:
        a.json.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    errors = sum("error" in r for r in rows)
    print(f"\n{len(rows) - errors}/{len(rows)} imported", file=sys.stderr)


if __name__ == "__main__":
    _main()
