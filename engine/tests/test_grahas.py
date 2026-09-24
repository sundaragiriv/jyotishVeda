import pytest
import swisseph as swe

from astro_core.grahas import NAKSHATRA_SPAN, PADA_SPAN, classify, compute_graha_positions

TS, LAT, LON = "1990-08-15T04:30:00Z", 17.385, 78.4867  # Hyderabad


# --- Division boundaries (pure maths) --------------------------------------

@pytest.mark.parametrize("lon, rasi, nak, pada", [
    (0.0,                    1,  1, 1),   # Ashwini 1, Mesha 0°
    (PADA_SPAN,              1,  1, 2),   # exactly Ashwini pada 2
    (NAKSHATRA_SPAN,         1,  2, 1),   # exactly Bharani 1
    (30.0,                   2,  3, 2),   # Vrishabha 0° = Krittika 2
    (120.0,                  5, 10, 1),   # Simha 0° = Magha 1 (gandanta junction)
    (359.9999,              12, 27, 4),   # Revati 4
    (360.0,                  1,  1, 1),   # wraps to Mesha
])
def test_classify_boundaries(lon, rasi, nak, pada):
    c = classify(lon)
    assert (c["rasi_index"], c["nakshatra_index"], c["pada"]) == (rasi, nak, pada)


def test_nakshatra_lords_cycle():
    assert classify(0.0)["nakshatra_lord"] == "Ketu"            # Ashwini
    assert classify(9 * NAKSHATRA_SPAN)["nakshatra_lord"] == "Ketu"  # Magha
    assert classify(26 * NAKSHATRA_SPAN)["nakshatra_lord"] == "Budha"  # Revati


# --- Ephemeris-backed checks -----------------------------------------------

def _by_name(res):
    return {g["graha"]: g for g in res["grahas"]}


def test_returns_nine_grahas():
    g = _by_name(compute_graha_positions(TS, LAT, LON))
    assert list(g) == ["Surya", "Chandra", "Mangala", "Budha", "Guru",
                       "Shukra", "Shani", "Rahu", "Ketu"]


@pytest.mark.parametrize("node", ["mean", "true"])
def test_ketu_opposite_rahu(node):
    g = _by_name(compute_graha_positions(TS, LAT, LON, node=node))
    diff = (g["Ketu"]["longitude"] - g["Rahu"]["longitude"]) % 360
    assert diff == pytest.approx(180.0, abs=1e-6)


def test_mean_node_always_retrograde():
    g = _by_name(compute_graha_positions(TS, LAT, LON))
    assert g["Rahu"]["retrograde"] and g["Ketu"]["retrograde"]
    assert not g["Surya"]["retrograde"] and not g["Chandra"]["retrograde"]


def test_sidereal_equals_tropical_minus_ayanamsha():
    res = compute_graha_positions(TS, LAT, LON)
    jd = res["julian_day_ut"]
    trop = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    sid = _by_name(res)["Surya"]["longitude"]
    ayan = res["settings"]["ayanamsha_value"]
    assert ((trop - ayan) % 360) == pytest.approx(sid, abs=1e-5)


def test_lahiri_ayanamsha_at_j2000():
    # Lahiri ayanamsha on 2000-01-01 is ~23°51' (23.85°)
    res = compute_graha_positions("2000-01-01T12:00:00Z", 0, 0)
    assert res["settings"]["ayanamsha_value"] == pytest.approx(23.85, abs=0.01)


def test_makara_sankranti_2024():
    # Sidereal Sun entered Makara around 2024-01-14 21:15 UTC
    before = _by_name(compute_graha_positions("2024-01-14T12:00:00Z", LAT, LON))
    after = _by_name(compute_graha_positions("2024-01-15T12:00:00Z", LAT, LON))
    assert before["Surya"]["rasi"] == "Dhanu"
    assert after["Surya"]["rasi"] == "Makara"


def test_geocentric_ignores_observer_location():
    a = _by_name(compute_graha_positions(TS, LAT, LON))
    b = _by_name(compute_graha_positions(TS, -33.87, 151.21))
    assert a["Chandra"]["longitude"] == b["Chandra"]["longitude"]


def test_rejects_naive_timestamp():
    with pytest.raises(ValueError):
        compute_graha_positions("1990-08-15T04:30:00", LAT, LON)
