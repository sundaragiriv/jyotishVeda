from datetime import datetime

import pytest

from panchang.panchang import compute_panchang, karana_name

HYD = (17.385, 78.4867, "Asia/Kolkata")


def _t(s):
    return datetime.fromisoformat(s)


@pytest.fixture(scope="module")
def ugadi_2024():
    return compute_panchang("2024-04-09", *HYD)


def test_ugadi_2024_is_chaitra_shukla_pratipada(ugadi_2024):
    p = ugadi_2024
    assert p["masa"]["name"] == "Chaitra" and not p["masa"]["adhika"]
    first = p["tithi"][0]
    assert (first["name"], first["paksha"]) == ("Pratipada", "Shukla")
    # Amavasya ended ~23:50 IST on 8 April 2024 (published panchangs)
    assert first["start"].startswith("2024-04-08T23:5")
    assert p["vara"]["name"] == "Mangalavara"


def test_nakshatra_revati_ends_morning(ugadi_2024):
    rev = ugadi_2024["nakshatra"][0]
    assert rev["name"] == "Revati"
    assert rev["end"].startswith("2024-04-09T07:3")


def test_spans_are_contiguous_and_cover_the_day(ugadi_2024):
    p = ugadi_2024
    for limb in ("tithi", "nakshatra", "yoga", "karana"):
        spans = p[limb]
        assert _t(spans[0]["start"]) <= _t(p["sunrise"])
        assert _t(spans[-1]["end"]) >= _t(p["next_sunrise"])
        for a, b in zip(spans, spans[1:]):
            assert abs((_t(b["start"]) - _t(a["end"])).total_seconds()) <= 1


def test_rahu_kalam_tuesday_is_seventh_eighth(ugadi_2024):
    p = ugadi_2024
    rise, sset = _t(p["sunrise"]), _t(p["sunset"])
    eighth = (sset - rise) / 8
    assert abs((_t(p["rahu_kalam"]["start"]) - (rise + 6 * eighth)).total_seconds()) <= 1
    assert abs((_t(p["yamagandam"]["start"]) - (rise + 2 * eighth)).total_seconds()) <= 1
    assert abs((_t(p["gulika_kalam"]["start"]) - (rise + 4 * eighth)).total_seconds()) <= 1


def test_adhika_shravana_2023():
    # 2023 had Adhika Shravana (approx. 18 Jul - 16 Aug 2023)
    m = compute_panchang("2023-07-25", *HYD)["masa"]
    assert (m["name"], m["adhika"]) == ("Shravana", True)
    m2 = compute_panchang("2023-08-25", *HYD)["masa"]
    assert (m2["name"], m2["adhika"]) == ("Shravana", False)   # nija Shravana


def test_hindu_sunrise_is_later_than_upper_limb():
    a = _t(compute_panchang("2024-04-09", *HYD)["sunrise"])
    b = _t(compute_panchang("2024-04-09", *HYD, sunrise="hindu")["sunrise"])
    assert 60 < (b - a).total_seconds() < 600


def test_karana_names():
    assert karana_name(0) == "Kimstughna"
    assert [karana_name(k) for k in range(1, 8)] == \
        ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
    assert karana_name(56) == "Vishti"
    assert [karana_name(k) for k in (57, 58, 59)] == ["Shakuni", "Chatushpada", "Naga"]


def test_rejects_unknown_sunrise_mode():
    with pytest.raises(ValueError):
        compute_panchang("2024-04-09", *HYD, sunrise="bogus")
