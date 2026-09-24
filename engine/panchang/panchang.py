"""
Panchang — the five limbs of the Hindu day, for a place and civil date.

    Vara       weekday; the Hindu day runs sunrise to next sunrise (Udaya)
    Tithi      each 12° of Moon−Sun elongation (30 per lunar month)
    Nakshatra  Moon's sidereal position in 27 divisions of 13°20'
    Yoga       each 13°20' of (Moon + Sun) sidereal longitude
    Karana     each 6° of elongation (half a tithi; 60 per lunar month)

Plus sunrise/sunset, Rahu Kalam, Yamagandam, Gulika Kalam (day from
sunrise to sunset split into 8 equal parts) and the amanta lunar month
(masa), with adhika (intercalary) detection.

Every limb is reported as the list of spans that touch the Hindu day
(sunrise to next sunrise), each with exact start and end times, so a
tithi that ends at 09:41 and the next one are both visible.

Settings (explicit, never silent):
    sunrise   "upper_limb" (default): upper limb with refraction, as in
              published sunrise tables; "center": disc centre with
              refraction; "hindu": Swiss Ephemeris BIT_HINDU_RISING
              (disc centre, no refraction), the classical Surya Siddhanta
              style definition.
    ayanamsha Lahiri by default (affects nakshatra, yoga and masa; tithi
              and karana depend only on elongation and are ayanamsha-free).

Masa rule (amanta, as used in Andhra/Telangana, Karnataka, Maharashtra):
    a lunar month runs new moon to new moon and is named from the sidereal
    rasi of the Sun at the new moon that begins it: Sun in Meena -> Chaitra,
    Mesha -> Vaishakha, ... If the Sun is in the same rasi at both bounding
    new moons (no sankranti inside the month), the month is adhika.
    Kshaya months (two sankrantis in one month) are flagged, not named.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import swisseph as swe

from astro_core.grahas import NAKSHATRAS, RASIS, jd_to_utc, julian_day_ut

# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------

VARAS = ["Ravivara", "Somavara", "Mangalavara", "Budhavara",
         "Guruvara", "Shukravara", "Shanivara"]

_TITHI_BASE = ["Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
               "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
               "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi"]
TITHIS = _TITHI_BASE + ["Purnima"] + _TITHI_BASE + ["Amavasya"]

YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
         "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
         "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
         "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
         "Shukla", "Brahma", "Indra", "Vaidhriti"]

_CHARA_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]

MASAS = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana",
         "Bhadrapada", "Ashvayuja", "Kartika", "Margashira", "Pausha",
         "Magha", "Phalguna"]

# 1-based eighth of daytime, indexed by vara (0 = Ravivara)
RAHU_KALAM = [8, 2, 7, 5, 6, 4, 3]
YAMAGANDAM = [5, 4, 3, 2, 1, 7, 6]
GULIKA_KALAM = [7, 6, 5, 4, 3, 2, 1]

SUNRISE_MODES = {
    "upper_limb": 0,
    "center": swe.BIT_DISC_CENTER,
    "hindu": swe.BIT_HINDU_RISING,
}

NAK_SPAN = 360.0 / 27.0


def karana_name(k: int) -> str:
    """k = 0..59, the karana index within the lunar month."""
    if k == 0:
        return "Kimstughna"
    if k >= 57:
        return ["Shakuni", "Chatushpada", "Naga"][k - 57]
    return _CHARA_KARANAS[(k - 1) % 7]


# ---------------------------------------------------------------------------
# Astronomy helpers
# ---------------------------------------------------------------------------

def _sid(jd: float, body: int) -> float:
    return swe.calc_ut(jd, body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]


def _elongation(jd: float) -> float:
    return (_sid(jd, swe.MOON) - _sid(jd, swe.SUN)) % 360.0


LIMBS = {
    # name: (angle function, span in degrees, count, namer)
    "tithi": (_elongation, 12.0, 30, lambda i: TITHIS[i]),
    "nakshatra": (lambda jd: _sid(jd, swe.MOON), NAK_SPAN, 27, lambda i: NAKSHATRAS[i]),
    "yoga": (lambda jd: (_sid(jd, swe.MOON) + _sid(jd, swe.SUN)) % 360.0,
             NAK_SPAN, 27, lambda i: YOGAS[i]),
    "karana": (_elongation, 6.0, 60, karana_name),
}


def _next_crossing(f, target: float, jd_start: float, step: float = 0.25,
                   max_days: float = 40.0, tol: float = 1e-7) -> float:
    """First JD after jd_start where the increasing angle f passes target."""
    def g(t):
        return (f(t) - target + 180.0) % 360.0 - 180.0

    lo, glo = jd_start, g(jd_start)
    t = jd_start
    while t - jd_start < max_days:
        hi = t + step
        ghi = g(hi)
        if glo < 0 <= ghi and ghi - glo < 180:
            break
        lo, glo, t = hi, ghi, hi
    else:
        raise RuntimeError("crossing not found")
    while hi - lo > tol:                       # bisection, ~0.01 s precision
        mid = (lo + hi) / 2
        if g(mid) < 0:
            lo = mid
        else:
            hi = mid
    return hi


def _ephemeris_used(jd: float) -> str:
    flag = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[1]
    return ("Swiss Ephemeris (data files)" if flag & swe.FLG_SWIEPH
            else "Moshier (built-in analytical)")


def _sun_event(jd: float, lat: float, lon: float, alt: float, rise: bool, mode: str) -> float:
    flag = (swe.CALC_RISE if rise else swe.CALC_SET) | SUNRISE_MODES[mode]
    res, tret = swe.rise_trans(jd, swe.SUN, flag, (lon, lat, alt))
    if res != 0:
        raise ValueError("Sun does not rise/set on this date at this latitude")
    return tret[0]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def compute_panchang(
    on: date | str,
    latitude: float,
    longitude: float,
    tz: str,
    *,
    altitude_m: float = 0.0,
    sunrise: str = "upper_limb",
    ayanamsha: int = swe.SIDM_LAHIRI,
) -> dict:
    if isinstance(on, str):
        on = date.fromisoformat(on)
    if sunrise not in SUNRISE_MODES:
        raise ValueError(f"sunrise must be one of {sorted(SUNRISE_MODES)}")
    zone = ZoneInfo(tz)
    swe.set_sid_mode(ayanamsha, 0, 0)

    def local(jd: float) -> str:
        return jd_to_utc(jd).astimezone(zone).isoformat(timespec="seconds")

    midnight = datetime.combine(on, time(0), tzinfo=zone)
    jd0 = julian_day_ut(midnight)
    jd_rise = _sun_event(jd0, latitude, longitude, altitude_m, True, sunrise)
    jd_set = _sun_event(jd_rise, latitude, longitude, altitude_m, False, sunrise)
    jd_next_rise = _sun_event(jd_set, latitude, longitude, altitude_m, True, sunrise)

    vara_idx = (on.weekday() + 1) % 7          # Python Monday=0 -> Ravivara=0

    limbs = {}
    for name, (f, span, count, namer) in LIMBS.items():
        spans = []
        t = jd_rise
        prev_end = None
        while t < jd_next_rise:
            idx = int(f(t + 1e-9) // span) % count
            end = _next_crossing(f, ((idx + 1) * span) % 360.0, t)
            # the first span began before sunrise: find its true start;
            # later spans start exactly where the previous one ended
            start = prev_end if spans else _next_crossing(f, (idx * span) % 360.0, t - 2.0)
            spans.append({"index": idx + 1, "name": namer(idx),
                          "start": local(start), "end": local(end)})
            prev_end = end
            t = end + 1e-8
        limbs[name] = spans
    for s in limbs["tithi"]:
        s["paksha"] = "Shukla" if s["index"] <= 15 else "Krishna"

    # Kalams: eighths of daytime
    part = (jd_set - jd_rise) / 8.0

    def kalam(table):
        k = table[vara_idx] - 1
        return {"start": local(jd_rise + k * part), "end": local(jd_rise + (k + 1) * part)}

    # Masa (amanta)
    elong = _elongation(jd_rise)
    prev_nm = _next_crossing(_elongation, 0.0, jd_rise - elong / 11.0 - 2.0)
    if prev_nm > jd_rise:                      # safety: step back one more month
        prev_nm = _next_crossing(_elongation, 0.0, prev_nm - 32.0)
    next_nm = _next_crossing(_elongation, 0.0, jd_rise + 1e-6)
    r_start = int(_sid(prev_nm, swe.SUN) // 30) % 12
    r_end = int(_sid(next_nm, swe.SUN) // 30) % 12
    sankrantis = (r_end - r_start) % 12
    masa = {
        "name": MASAS[(r_start + 1) % 12],
        "system": "amanta",
        "adhika": sankrantis == 0,
        "kshaya_warning": sankrantis >= 2,
        "sun_rasi_at_start": RASIS[r_start],
        "starts": local(prev_nm),
        "ends": local(next_nm),
    }

    return {
        "date": on.isoformat(),
        "location": {"latitude": latitude, "longitude": longitude,
                     "altitude_m": altitude_m, "tz": tz},
        "settings": {"sunrise": sunrise, "ayanamsha": swe.get_ayanamsa_name(ayanamsha),
                     "month_system": "amanta", "ephemeris": _ephemeris_used(jd_rise)},
        "sunrise": local(jd_rise),
        "sunset": local(jd_set),
        "next_sunrise": local(jd_next_rise),
        "vara": {"index": vara_idx + 1, "name": VARAS[vara_idx]},
        **limbs,
        "rahu_kalam": kalam(RAHU_KALAM),
        "yamagandam": kalam(YAMAGANDAM),
        "gulika_kalam": kalam(GULIKA_KALAM),
        "masa": masa,
    }
