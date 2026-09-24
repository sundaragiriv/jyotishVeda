"""
Canonical birth record — the platform's own model.

Every importer (JHora .jhd today; others later) converts INTO this model.
Nothing downstream reads a foreign format directly.

Improvements over legacy formats:
  * Signed, unambiguous units (decimal degrees, East/North positive,
    UTC offset in seconds, East positive).
  * Time standard is explicit: a zone offset vs Local Mean Time (LMT).
  * Birth-time accuracy is recorded (drives rectification / confidence).
  * Provenance is kept: source format, file, raw fields, import warnings.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TimeStandard(str, Enum):
    ZONE = "zone"        # a civil time-zone offset (e.g. IST +05:30)
    LMT = "lmt"          # local mean time, offset = longitude / 15
    UNKNOWN = "unknown"


class TimeAccuracy(str, Enum):
    EXACT = "exact"              # recorded to the minute or better
    APPROXIMATE = "approximate"
    RECTIFIED = "rectified"
    UNKNOWN = "unknown"


class Place(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90, description="decimal deg, North +")
    longitude: float = Field(..., ge=-180, le=180, description="decimal deg, East +")
    altitude_m: float = 0.0


class Provenance(BaseModel):
    source_format: str                     # e.g. "jhora.jhd"
    source_file: Optional[str] = None
    raw_fields: list[str] = []
    warnings: list[str] = []


class BirthRecord(BaseModel):
    name: str
    local_datetime: datetime               # naive wall-clock time at birth place
    utc_offset_seconds: int                # East +, e.g. IST = 19800
    time_standard: TimeStandard = TimeStandard.UNKNOWN
    timezone_iana: Optional[str] = None    # set when known; never guessed
    time_accuracy: TimeAccuracy = TimeAccuracy.UNKNOWN
    place: Place
    provenance: Optional[Provenance] = None

    @field_validator("local_datetime")
    @classmethod
    def _naive(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            raise ValueError("local_datetime must be naive wall-clock time")
        return v

    @property
    def utc_datetime(self) -> datetime:
        return (self.local_datetime - timedelta(seconds=self.utc_offset_seconds)
                ).replace(tzinfo=timezone.utc)
