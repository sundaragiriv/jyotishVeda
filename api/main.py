"""
Jyotisha Veda API v1 — a thin HTTP layer over the engine.

    GET  /v1/health
    POST /v1/chart        birth data -> grahas, lagna, bhavas, vargas, dasha
    GET  /v1/panchang     date + place -> five limbs, kalams, masa
    POST /v1/import/jhd   JHora .jhd text -> BirthRecord (+ warnings)
    GET  /v1/places       place search -> lat, lon, IANA zone

Run:  uvicorn main:app --reload     (with the engine installed: pip install -e ../engine)

Birth time input accepts either an absolute UTC instant, or local wall-clock
time plus an IANA zone (historical offsets and DST resolved from tzdata) or
an explicit UTC offset. Whichever is used, the response echoes the UTC
instant actually computed, so there is never doubt about the input.

Note: Swiss Ephemeris keeps the sidereal mode as process-global state. Each
request sets it before computing, and a lock serialises the calculation so
concurrent requests with different ayanamshas cannot interfere.
"""

from __future__ import annotations

import threading
from datetime import date, datetime, timedelta, timezone
from typing import Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from astro_core.grahas import compute_graha_positions
from astro_core.lagna import bhava_of, compute_lagna, whole_sign_house
from dasha.vimshottari import active_periods, compute_vimshottari
from importers.jhd import JhdImportError, parse_jhd
from panchang.panchang import compute_panchang
from vargas.shodashvarga import SHODASHVARGA, compute_vargas

import places

API_VERSION = "0.1.0"

AYANAMSHAS = {
    "lahiri": swe.SIDM_LAHIRI,
    "true_chitra": swe.SIDM_TRUE_CITRA,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
}

_LOCK = threading.Lock()

app = FastAPI(title="Jyotisha Veda API", version=API_VERSION)

# Web front-ends allowed to call the API (comma-separated in JV_CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("JV_CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class BirthInput(BaseModel):
    utc: Optional[datetime] = Field(None, description="aware instant, e.g. 1990-08-15T04:30:00Z")
    local_datetime: Optional[datetime] = Field(None, description="naive wall-clock time")
    tz: Optional[str] = Field(None, description="IANA zone, e.g. Asia/Kolkata")
    utc_offset_minutes: Optional[float] = Field(None, ge=-840, le=840, description="East positive")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude_m: float = 0.0

    @model_validator(mode="after")
    def _one_time_form(self):
        if self.utc is not None:
            if self.utc.tzinfo is None:
                raise ValueError("utc must include a zone designator (Z or +hh:mm)")
            if self.local_datetime is not None:
                raise ValueError("give either utc or local_datetime, not both")
        else:
            if self.local_datetime is None:
                raise ValueError("give utc, or local_datetime with tz or utc_offset_minutes")
            if self.local_datetime.tzinfo is not None:
                raise ValueError("local_datetime must be wall-clock time without an offset; "
                                 "use utc for an absolute instant")
            if (self.tz is None) == (self.utc_offset_minutes is None):
                raise ValueError("local_datetime needs exactly one of tz or utc_offset_minutes")
        return self

    def resolve_utc(self) -> datetime:
        if self.utc is not None:
            return self.utc.astimezone(timezone.utc)
        local = self.local_datetime.replace(tzinfo=None)
        if self.tz is not None:
            try:
                zone = ZoneInfo(self.tz)
            except ZoneInfoNotFoundError:
                raise ValueError(f"unknown time zone {self.tz!r}")
            early = local.replace(tzinfo=zone, fold=0)
            late = local.replace(tzinfo=zone, fold=1)
            if early.utcoffset() != late.utcoffset():
                # the clock was changed around this time: never guess
                roundtrip = early.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
                kind = "does not exist (clocks skipped it)" if roundtrip != local \
                    else "occurs twice (clocks fell back)"
                offs = sorted({int(x.utcoffset().total_seconds() // 60) for x in (early, late)})
                raise ValueError(f"{local.isoformat()} in {self.tz} {kind}; "
                                 f"resend with utc_offset_minutes (one of {offs})")
            return early.astimezone(timezone.utc)
        return (local - timedelta(minutes=self.utc_offset_minutes)).replace(tzinfo=timezone.utc)


class ChartOptions(BaseModel):
    ayanamsha: Literal["lahiri", "true_chitra", "raman", "krishnamurti"] = "lahiri"
    node: Literal["mean", "true"] = "mean"
    topocentric: bool = False
    house_system: Literal["W", "S", "P", "K", "O", "R", "C", "E", "B"] = "W"
    vargas: list[int] = Field(default_factory=lambda: list(SHODASHVARGA))
    # full trees beyond 3 levels are ~10 MB; deeper levels belong to a
    # separate on-demand endpoint for a single period
    dasha_depth: int = Field(2, ge=1, le=3)
    year_length: Literal["gregorian", "julian", "sidereal", "savana"] = "gregorian"


class ChartRequest(BaseModel):
    birth: BirthInput
    options: ChartOptions = ChartOptions()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/v1/health")
def health():
    return {"status": "ok", "api_version": API_VERSION, "swisseph": swe.version}


@app.post("/v1/chart")
def chart(req: ChartRequest):
    b, o = req.birth, req.options
    try:
        utc = b.resolve_utc()
    except ValueError as e:
        raise HTTPException(422, str(e))
    bad = [n for n in o.vargas if n not in SHODASHVARGA]
    if bad:
        raise HTTPException(422, f"unsupported vargas {bad}; allowed {SHODASHVARGA}")
    sid = AYANAMSHAS[o.ayanamsha]

    try:
        with _LOCK:
            pos = compute_graha_positions(utc, b.latitude, b.longitude, altitude_m=b.altitude_m,
                                          node=o.node, topocentric=o.topocentric, ayanamsha=sid)
            lag = compute_lagna(utc, b.latitude, b.longitude,
                                house_system=o.house_system, ayanamsha=sid)
    except Exception as e:                       # e.g. invalid house-system code
        raise HTTPException(422, f"calculation failed: {e}")

    lagna = lag["lagna"]
    starts = lag.get("bhava_sandhi") or lag.get("bhava_start")
    for g in pos["grahas"]:
        g["house"] = whole_sign_house(lagna["rasi_index"], g["rasi_index"])
        if starts:
            g["bhava"] = bhava_of(g["longitude"], starts)

    lons = {g["graha"]: g["longitude"] for g in pos["grahas"]}
    lons["Lagna"] = lagna["longitude"]
    moon = lons["Chandra"]
    dasha = compute_vimshottari(moon, utc, depth=o.dasha_depth, year_length=o.year_length)

    return {
        "input": {**pos["input"], "utc": utc.isoformat().replace("+00:00", "Z")},
        "settings": {**pos["settings"], "house_system": o.house_system,
                     "year_length": o.year_length},
        "julian_day_ut": pos["julian_day_ut"],
        "lagna": lagna,
        "mc": lag["mc"],
        "bhavas": {k: v for k, v in lag.items()
                   if k in ("bhava_sandhi", "bhava_madhya", "bhava_start")},
        "grahas": pos["grahas"],
        "vargas": compute_vargas(lons, o.vargas),
        "dasha": {**dasha, "current": active_periods(dasha, datetime.now(timezone.utc))},
    }


@app.get("/v1/panchang")
def panchang(
    on: date = Query(..., alias="date"),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    tz: str = Query(..., description="IANA zone, e.g. Asia/Kolkata"),
    altitude_m: float = 0.0,
    sunrise: Literal["upper_limb", "center", "hindu"] = "upper_limb",
    ayanamsha: Literal["lahiri", "true_chitra", "raman", "krishnamurti"] = "lahiri",
):
    try:
        ZoneInfo(tz)
    except ZoneInfoNotFoundError:
        raise HTTPException(422, f"unknown time zone {tz!r}")
    try:
        with _LOCK:
            return compute_panchang(on, latitude, longitude, tz, altitude_m=altitude_m,
                                    sunrise=sunrise, ayanamsha=AYANAMSHAS[ayanamsha])
    except ValueError as e:                      # e.g. polar day/night
        raise HTTPException(422, str(e))


class JhdUpload(BaseModel):
    name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=10_000)


@app.post("/v1/import/jhd")
def import_jhd(body: JhdUpload):
    try:
        imp = parse_jhd(body.content, body.name)
    except JhdImportError as e:
        raise HTTPException(422, str(e))
    out = imp.model_dump(mode="json")
    out["record"]["utc_datetime"] = imp.record.utc_datetime.isoformat()
    return out



@app.get("/v1/places")
def place_search(q: str = Query(..., min_length=2, max_length=80),
                 limit: int = Query(8, ge=1, le=20)):
    return {"results": places.search(q, limit), "attribution": places.ATTRIBUTION}
