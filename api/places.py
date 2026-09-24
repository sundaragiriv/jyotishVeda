"""
Place search for birth-data entry: name -> latitude, longitude, IANA zone.

Data: GeoNames cities with population >= 1000 (~170k places), via the
geonamescache package (GeoNames data, CC BY 4.0 — attribution required
in the UI). Loaded once, lazily. Matching is accent- and case-insensitive
on the name and ASCII alternate names ("Tirupathi", "Bombay"); results are
ranked exact > prefix, then by population.
"""

from __future__ import annotations

import threading
import unicodedata
from functools import lru_cache

import geonamescache

ATTRIBUTION = "Place data © GeoNames (geonames.org), CC BY 4.0"

_lock = threading.Lock()
_index: list[tuple[tuple[str, ...], dict]] | None = None


def fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


def _load() -> list[tuple[tuple[str, ...], dict]]:
    global _index
    with _lock:
        if _index is None:
            gc = geonamescache.GeonamesCache(min_city_population=1000)
            countries = {k: v["name"] for k, v in gc.get_countries().items()}
            us_states = {k: v for k, v in gc.get_us_states().items()}
            rows = []
            for c in gc.get_cities().values():
                keys = {fold(c["name"])}
                keys |= {fold(a) for a in c.get("alternatenames", []) if a.isascii() and a}
                region = c["countrycode"]
                if region == "US" and c.get("admin1code") in us_states:
                    region = f"{c['admin1code']}, US"
                rows.append((tuple(k for k in keys if k), {
                    "id": c["geonameid"],
                    "name": c["name"],
                    "region": region,
                    "country": countries.get(c["countrycode"], c["countrycode"]),
                    "latitude": c["latitude"],
                    "longitude": c["longitude"],
                    "timezone": c["timezone"],
                    "population": c["population"],
                }))
            _index = rows
    return _index


@lru_cache(maxsize=2048)
def search(q: str, limit: int = 8) -> list[dict]:
    q = fold(q)
    if len(q) < 2:
        return []
    exact, prefix = [], []
    for keys, place in _load():
        if q in keys:
            exact.append(place)
        elif any(k.startswith(q) for k in keys):
            prefix.append(place)
    by_pop = lambda p: -p["population"]
    return (sorted(exact, key=by_pop) + sorted(prefix, key=by_pop))[:limit]
