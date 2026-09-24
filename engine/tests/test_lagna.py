import pytest

from astro_core.grahas import jd_to_utc, julian_day_ut
from astro_core.lagna import bhava_of, compute_lagna, whole_sign_house

VIVEKANANDA = ("1863-01-12T00:39:00Z", 22.6667, 88.5)   # Kolkata, LMT 6:33


def test_vivekananda_dhanu_lagna():
    # Widely published: Dhanu lagna; also matches JHora's cached value 265.99°
    lg = compute_lagna(*VIVEKANANDA)["lagna"]
    assert lg["rasi"] == "Dhanu"
    assert lg["longitude"] == pytest.approx(265.98, abs=0.05)


def test_sripati_first_madhya_is_lagna():
    r = compute_lagna(*VIVEKANANDA, house_system="S")
    assert r["bhava_madhya"][0] == pytest.approx(r["lagna"]["longitude"], abs=1e-6)
    # sandhi 1 lies before the lagna, sandhi 2 after it
    assert bhava_of(r["lagna"]["longitude"], r["bhava_sandhi"]) == 1


def test_whole_sign_house():
    assert whole_sign_house(9, 9) == 1     # same rasi as lagna
    assert whole_sign_house(9, 10) == 2
    assert whole_sign_house(9, 8) == 12
    assert whole_sign_house(1, 12) == 12


def test_bhava_of_wraps_zero():
    starts = [350 + 30 * i for i in range(12)]
    starts = [s % 360 for s in starts]
    assert bhava_of(355, starts) == 1
    assert bhava_of(5, starts) == 1
    assert bhava_of(21, starts) == 2
    assert bhava_of(349, starts) == 12


def test_jd_roundtrip():
    ts = "2024-01-15T06:30:15.250Z"
    assert jd_to_utc(julian_day_ut(ts)).isoformat() == "2024-01-15T06:30:15.250000+00:00"
