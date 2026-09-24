from datetime import datetime, timedelta, timezone

import pytest

from dasha.vimshottari import NAK_SPAN, YEARS, active_periods, compute_vimshottari

BIRTH = datetime(1990, 8, 15, 4, 30, tzinfo=timezone.utc)
P = datetime.fromisoformat


def test_years_total_120():
    assert sum(YEARS.values()) == 120


def test_start_of_ashwini_full_ketu_balance():
    d = compute_vimshottari(0.0, BIRTH, depth=1)
    assert d["starting_lord"] == "Ketu"
    assert d["balance_at_birth"]["years"] == pytest.approx(7.0)
    assert P(d["periods"][0]["start"]) == BIRTH


def test_half_rohini_gives_half_chandra():
    # Rohini (4th nakshatra) -> Chandra; mid-point -> 5 of 10 years left
    moon = 3 * NAK_SPAN + NAK_SPAN / 2
    d = compute_vimshottari(moon, BIRTH, depth=1)
    assert d["starting_lord"] == "Chandra"
    assert d["balance_at_birth"]["years"] == pytest.approx(5.0)
    assert [p["lord"] for p in d["periods"]] == \
        ["Chandra", "Mangala", "Rahu", "Guru", "Shani", "Budha", "Ketu", "Shukra", "Surya"]


def test_magha_and_mula_are_ketu():
    assert compute_vimshottari(9 * NAK_SPAN + 1, BIRTH, depth=1)["starting_lord"] == "Ketu"
    assert compute_vimshottari(18 * NAK_SPAN + 1, BIRTH, depth=1)["starting_lord"] == "Ketu"


def test_subperiods_tile_parent_exactly():
    d = compute_vimshottari(48.63, BIRTH, depth=3)
    for md in d["periods"]:
        ads = md["periods"]
        assert ads[0]["lord"] == md["lord"]                 # starts with own lord
        assert ads[0]["start"] == md["start"]
        assert abs((P(ads[-1]["end"]) - P(md["end"])).total_seconds()) < 1
        for a, b in zip(ads, ads[1:]):
            assert abs((P(b["start"]) - P(a["end"])).total_seconds()) < 1
        assert sum(a["years"] for a in ads) == pytest.approx(md["years"])


def test_antardasha_length_formula():
    d = compute_vimshottari(0.0, BIRTH, depth=2)
    ketu = d["periods"][0]
    shukra_in_ketu = ketu["periods"][1]
    assert shukra_in_ketu["lord"] == "Shukra"
    assert shukra_in_ketu["years"] == pytest.approx(7 * 20 / 120)   # 1y 2m


def test_total_cycle_is_120_years():
    d = compute_vimshottari(123.4, BIRTH, depth=1, year_length="julian")
    span = P(d["periods"][-1]["end"]) - P(d["periods"][0]["start"])
    assert span == timedelta(days=120 * 365.25)


def test_active_periods_chain():
    d = compute_vimshottari(48.63, BIRTH, depth=3)
    chain = active_periods(d, BIRTH + timedelta(days=1))
    assert [c["level"] for c in chain] == ["mahadasha", "antardasha", "pratyantardasha"]
    assert chain[0]["lord"] == d["starting_lord"]


def test_requires_aware_datetime():
    with pytest.raises(ValueError):
        compute_vimshottari(10.0, datetime(1990, 1, 1))
