import pytest

from importers.jhd import JhdImportError, parse_jhd
from models.birth import TimeStandard
from tools.jhd_audit import crosscheck

INDIA_A = """8
15
1947
0.000167
-5.300000
-77.130000
28.400000
0.000000
-5.500000
-5.500000
0
105
Delhi
India
"""

GANDHI_LMT = """10
2
1869
7.200000
-4.392667
-69.490000
21.370000
0.000000
-4.654444
-4.654444
0
0
Unknown
Unknown
"""

VIVEKANANDA_B = """1
12
1863
6.3300
-5.54
-88.30
22.40
0.439521
269.439396
167.457261
6.339977
281.788615
184.030503
277.118934
163.590327
232.260043
265.993210
000000000
"""

SHORT = "8\n15\n1872\n5.1700\n-5.53\n-88.20\n22.30\n"


def test_layout_a_zone_time():
    imp = parse_jhd(INDIA_A, "India")
    r = imp.record
    assert imp.layout == "A"
    assert r.local_datetime.isoformat() == "1947-08-15T00:00:01"
    assert r.utc_offset_seconds == 19800
    assert r.time_standard is TimeStandard.ZONE
    assert (r.place.latitude, r.place.longitude) == pytest.approx((28.666667, 77.216667))
    assert (r.place.name, r.place.country) == ("Delhi", "India")
    assert r.provenance.warnings == []


def test_lmt_offset_matches_longitude():
    r = parse_jhd(GANDHI_LMT, "Gandhi").record
    assert r.time_standard is TimeStandard.LMT
    assert r.utc_offset_seconds == 4 * 3600 + 39 * 60 + 16    # 69°49'E / 15
    assert r.place.name is None                               # "Unknown" dropped


def test_short_layout():
    imp = parse_jhd(SHORT, "Aurobindo")
    assert imp.layout == "short"
    assert imp.record.local_datetime.isoformat() == "1872-08-15T05:17:00"


def test_layout_b_cached_longitudes_crosscheck():
    imp = parse_jhd(VIVEKANANDA_B, "Vivekananda")
    assert imp.layout == "B"
    assert imp.record.utc_datetime.isoformat() == "1863-01-12T00:39:00+00:00"
    assert imp.cached_longitudes["Lagna"] == pytest.approx(265.99321)
    cc = crosscheck(imp)
    # constant ayanamsha-type offset; planets agree once it is removed
    assert 30 < cc["offset_arcsec"] < 90
    slow = ["Surya", "Mangala", "Budha", "Guru", "Shukra", "Shani"]
    assert all(abs(cc["residual_arcsec"][k]) < 5 for k in slow)


def test_rejects_minutes_over_59():
    bad = SHORT.replace("5.1700", "5.7500")          # 5h 75m is not H.MM
    with pytest.raises(JhdImportError, match="not H.MM"):
        parse_jhd(bad, "bad")


def test_rejects_invalid_date():
    with pytest.raises(JhdImportError, match="invalid date"):
        parse_jhd(SHORT.replace("8\n15", "2\n30", 1), "bad")


def test_rejects_truncated_file():
    with pytest.raises(JhdImportError, match="at least 7 lines"):
        parse_jhd("8\n15\n1872\n", "bad")


def test_western_longitude_warns():
    west = SHORT.replace("-88.20", "74.00")
    r = parse_jhd(west, "west").record
    assert r.place.longitude == pytest.approx(-74.0)
    assert any("Western longitude" in w for w in r.provenance.warnings)
