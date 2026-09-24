# Jyotisha Veda — platform v0.2

Classical Vedic astrology: a calculation engine (Swiss Ephemeris + Parashari rules),
an API, and the **Jyotisha Veda** web app. The mobile app **ChitraGupta** (formerly
Telugu Darshini) lives in its own repo and uses the same API.

```
engine/
  astro_core/grahas.py      sidereal Navagraha, rasi / nakshatra / pada
  astro_core/lagna.py       Lagna, whole-sign houses, optional bhava cusps
  vargas/shodashvarga.py    D1–D60 (the 16 BPHS vargas)
  panchang/panchang.py      tithi, vara, nakshatra, yoga, karana with end times,
                            sunrise/sunset, Rahu/Yama/Gulika kalam, amanta masa + adhika
  dasha/vimshottari.py      maha / antar / pratyantar (engine supports 5 levels)
  models/birth.py           canonical BirthRecord
  importers/jhd.py          Jagannatha Hora .jhd adapter (optional, not a dependency)
  tools/jhd_audit.py        import + cross-check a folder of .jhd files
api/main.py                 /v1/health, /v1/chart, /v1/panchang, /v1/import/jhd, /v1/places
api/places.py               place search (GeoNames, lat/lon + IANA time zone)
web/                        Jyotisha Veda (Next.js 16, TypeScript, Tailwind 4)
  app/page.tsx              Chart: birth form, two chart panels (any of D1–D60),
                            South/North style, English/Sanskrit labels,
                            graha table, Vimshottari timeline
  app/panchang/page.tsx     Panchang for any place and date
  components/charts/        South and North Indian SVG chart renderers
```

## Run

```bash
pip install -e engine[test] && (cd engine && pytest)          # 108 tests
pip install -r api/requirements.txt && (cd api && pytest)     # 25 tests
cd api && uvicorn main:app --reload                           # http://localhost:8000/docs
cd web && npm install && npm run dev                          # http://localhost:3000
```

The web app reads the API address from `NEXT_PUBLIC_API_URL` (see `web/.env.example`);
the API allows the web origin via `JV_CORS_ORIGINS` (default `http://localhost:3000`).

For production accuracy install the Swiss Ephemeris data files (`.se1`, from Astrodienst)
and set `SE_EPHE_PATH`. Without them the built-in Moshier ephemeris is used; every
response says which one was used.

## Defaults (all configurable, all echoed in responses)

| Setting | Default | Options |
|---|---|---|
| Ayanamsha | Lahiri (true, incl. nutation) | true_chitra, raman, krishnamurti |
| Rahu/Ketu | Mean node | true node |
| Frame | Geocentric | topocentric |
| Houses | Whole sign (rasi chart) | Sripati (sandhi + madhya), Placidus, Koch, Porphyry, Regiomontanus, Campanus, Equal, Alcabitius |
| Sunrise | Upper limb + refraction | disc centre; Hindu (centre, no refraction) |
| Lunar month | Amanta | — |
| Dasha year | 365.2425 days | julian, sidereal, savana (360) |

Local birth times are resolved through IANA zones (historical offsets, DST). Times that
do not exist or occur twice at a DST change are rejected with the two possible offsets,
never guessed.

## Verification status

- Varga rules, karana sequence, kalam tables, masa/adhika rule, Vimshottari:
  checked against BPHS translations and published panchangs by an independent review.
- Panchang spot-checks vs drikpanchang.com (Indore, Delhi, New York): all within 1 minute;
  kshaya tithi and Adhika Shravana 2023 / Adhika Jyeshtha 2026 handled correctly.
- JHora sample charts: planets agree within ~4″ after removing a per-file ayanamsha offset
  (the old files were saved under differing settings).

## Open items

1. Confirm JHora 8.0's default ayanamsha variant and dasha year length with one live chart.
2. Pre-1582 dates are always Gregorian (no Julian-calendar input yet).
3. Next modules: Varjyam / Abhijit / Durmuhurtam, festivals (Telugu calendar rules),
   Jaimini karakas and chara dasha, Ashtakavarga, Shadbala.
