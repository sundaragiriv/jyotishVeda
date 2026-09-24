"""Regression tests for the independent review findings."""

import swisseph as swe
import pytest

from astro_core.grahas import classify, compute_graha_positions, jd_to_utc
from astro_core.lagna import compute_lagna
from importers.jhd import JhdImportError, parse_jhd
from panchang.panchang import compute_panchang
from vargas.shodashvarga import varga_position


def test_leap_second_jd_does_not_crash():
    jd = swe.utc_to_jd(2016, 12, 31, 23, 59, 60.5, swe.GREG_CAL)[1]
    assert jd_to_utc(jd).isoformat().startswith("2016-12-31T23:59:59")


def test_unknown_house_system_rejected():
    with pytest.raises(ValueError, match="house_system"):
        compute_lagna("1990-08-15T04:30:00Z", 17.385, 78.4867, house_system="Z")


def test_d1_varga_agrees_with_classify_at_wrap():
    lon = 359.9999999995
    assert varga_position(lon, 1)[0] + 1 == classify(lon)["rasi_index"]


def test_longitudes_not_prematurely_rounded():
    g = compute_graha_positions("1990-08-15T04:30:00Z", 17.385, 78.4867)["grahas"][1]
    assert g["longitude"] != round(g["longitude"], 6)


def test_ayanamsha_is_signed_in_antiquity():
    s = compute_graha_positions("0100-06-01T00:00:00Z", 0, 0)["settings"]
    assert s["ayanamsha_value"] < 0 and s["ayanamsha_dms"].startswith("-")


def test_jhd_non_numeric_field_is_import_error():
    lines = ["8", "15", "1947", "0.0", "-5.3", "-77.13", "28.4", "0", "-5.5", "-5.5",
             "0", "105", "Delhi", "India", "1", "abc", "20"]
    with pytest.raises(JhdImportError, match="pressure"):
        parse_jhd("\n".join(lines), "bad")


def test_panchang_spans_have_no_seams():
    # Previously a 1 s gap could appear between karanas (e.g. Helsinki 1999-03-15)
    p = compute_panchang("1999-03-15", 60.17, 24.94, "Europe/Helsinki")
    for limb in ("tithi", "nakshatra", "yoga", "karana"):
        for a, b in zip(p[limb], p[limb][1:]):
            assert a["end"] == b["start"]


def test_panchang_reports_ephemeris():
    assert "ephemeris" in compute_panchang("2024-04-09", 17.385, 78.4867, "Asia/Kolkata")["settings"]
