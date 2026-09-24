import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

HYD = {"latitude": 17.385, "longitude": 78.4867}


def chart(birth, **options):
    return client.post("/v1/chart", json={"birth": birth, "options": options})


def test_health():
    r = client.get("/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_chart_utc_input():
    r = chart({"utc": "1990-08-15T04:30:00Z", **HYD})
    assert r.status_code == 200, r.text
    d = r.json()
    assert len(d["grahas"]) == 9
    assert all(1 <= g["house"] <= 12 for g in d["grahas"])
    assert set(d["vargas"]["Lagna"]) >= {"D1", "D9", "D60"}
    assert d["dasha"]["starting_lord"] == "Chandra"      # Moon in Rohini


def test_local_time_with_iana_zone_equals_utc():
    a = chart({"utc": "1990-08-15T04:30:00Z", **HYD}).json()
    b = chart({"local_datetime": "1990-08-15T10:00:00", "tz": "Asia/Kolkata", **HYD}).json()
    assert a["input"]["utc"] == b["input"]["utc"]
    assert a["grahas"] == b["grahas"]


def test_local_time_with_offset():
    b = chart({"local_datetime": "1990-08-15T10:00:00", "utc_offset_minutes": 330, **HYD}).json()
    assert b["input"]["utc"] == "1990-08-15T04:30:00Z"


def test_dst_zone_resolved_historically():
    # New York in July is EDT (UTC-4)
    r = chart({"local_datetime": "2000-07-04T12:00:00", "tz": "America/New_York",
               "latitude": 40.71, "longitude": -74.0}).json()
    assert r["input"]["utc"] == "2000-07-04T16:00:00Z"


@pytest.mark.parametrize("birth", [
    {"local_datetime": "1990-08-15T10:00:00", **HYD},                              # no zone
    {"utc": "1990-08-15T04:30:00", **HYD},                                          # naive utc
    {"local_datetime": "1990-08-15T10:00:00", "tz": "Asia/Kolkata",
     "utc_offset_minutes": 330, **HYD},                                             # both
])
def test_ambiguous_time_input_rejected(birth):
    assert chart(birth).status_code == 422


def test_unknown_zone_rejected():
    r = chart({"local_datetime": "1990-08-15T10:00:00", "tz": "Mars/Olympus", **HYD})
    assert r.status_code == 422


def test_bad_varga_rejected():
    assert chart({"utc": "1990-08-15T04:30:00Z", **HYD}, vargas=[5]).status_code == 422


def test_sripati_bhavas():
    d = chart({"utc": "1990-08-15T04:30:00Z", **HYD}, house_system="S").json()
    assert len(d["bhavas"]["bhava_madhya"]) == 12
    assert all(1 <= g["bhava"] <= 12 for g in d["grahas"])


def test_ayanamsha_option_changes_positions():
    a = chart({"utc": "1990-08-15T04:30:00Z", **HYD}).json()
    b = chart({"utc": "1990-08-15T04:30:00Z", **HYD}, ayanamsha="raman").json()
    diff = a["grahas"][0]["longitude"] - b["grahas"][0]["longitude"]
    assert -2 < diff < -1            # Raman ayanamsha is ~1.4° smaller than Lahiri


def test_panchang_endpoint():
    r = client.get("/v1/panchang", params={"date": "2024-04-09", "tz": "Asia/Kolkata", **HYD})
    assert r.status_code == 200, r.text
    assert r.json()["masa"]["name"] == "Chaitra"


def test_panchang_polar_night_is_422():
    r = client.get("/v1/panchang", params={"date": "2024-12-21", "latitude": 78.2,
                                            "longitude": 15.6, "tz": "Arctic/Longyearbyen"})
    assert r.status_code == 422


def test_import_jhd():
    text = "1\n12\n1863\n6.3300\n-5.54\n-88.30\n22.40\n"
    r = client.post("/v1/import/jhd", json={"name": "Vivekananda", "content": text})
    assert r.status_code == 200, r.text
    assert r.json()["record"]["utc_datetime"] == "1863-01-12T00:39:00+00:00"


def test_import_jhd_bad_file():
    r = client.post("/v1/import/jhd", json={"name": "x", "content": "1\n2\n"})
    assert r.status_code == 422


# --- regressions from the independent review -------------------------------

@pytest.mark.parametrize("local, kind", [
    ("2024-03-10T02:30:00", "does not exist"),     # US spring-forward gap
    ("2024-11-03T01:30:00", "occurs twice"),       # US fall-back overlap
])
def test_dst_gap_and_overlap_rejected(local, kind):
    r = chart({"local_datetime": local, "tz": "America/New_York",
               "latitude": 40.71, "longitude": -74.0})
    assert r.status_code == 422 and kind in r.text


def test_aware_local_datetime_rejected():
    r = chart({"local_datetime": "2024-01-01T10:00:00+05:30", "utc_offset_minutes": 0, **HYD})
    assert r.status_code == 422


def test_offset_out_of_range_rejected():
    r = chart({"local_datetime": "2024-01-01T10:00:00", "utc_offset_minutes": 100000, **HYD})
    assert r.status_code == 422


def test_unknown_house_system_rejected():
    assert chart({"utc": "1990-08-15T04:30:00Z", **HYD}, house_system="Z").status_code == 422


def test_dasha_depth_capped():
    assert chart({"utc": "1990-08-15T04:30:00Z", **HYD}, dasha_depth=5).status_code == 422


# --- places -----------------------------------------------------------------

def test_places_accent_insensitive():
    r = client.get("/v1/places", params={"q": "machilipatnam"}).json()
    top = r["results"][0]
    assert top["name"].startswith("Machil") and top["timezone"] == "Asia/Kolkata"
    assert "GeoNames" in r["attribution"]


def test_places_alternate_name_and_ranking():
    names = [p["name"] for p in client.get("/v1/places", params={"q": "hyderabad"}).json()["results"]]
    assert names[0] == "Hyderabad"                       # India's (larger) first
    cary = client.get("/v1/places", params={"q": "cary"}).json()["results"][0]
    assert cary["region"] == "NC, US" and cary["timezone"] == "America/New_York"


def test_places_short_query_rejected():
    assert client.get("/v1/places", params={"q": "a"}).status_code == 422
