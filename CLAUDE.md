# Jyotisha Veda — project brief for Claude Code

## Products (one engine, three faces)

| Product | What it is | Where |
|---|---|---|
| **Jyotisha Veda** | Professional chart workstation — "Jagannatha Hora on turbo". Dense, fast, keyboard-first. | this repo, `web/` |
| **ChitraGupta** | Modern daily panchang app (Drik Panchang on turbo). Consumer, mobile. | separate repo (later) |
| **LMS** | Jyotisha courses, part of Jyotisha Veda but its own look. | later |

All three call the same API. **All astrology maths lives in `engine/`** — never compute
positions, dignities or periods in the frontend.

## Layout

```
engine/   Python calculation engine (pyswisseph). Pure functions + pytest.
api/      FastAPI over the engine. Endpoints in api/main.py.
web/      Next.js 16 + TypeScript + Tailwind 4 (read web/AGENTS.md: Next 16 differs from older docs).
docs/design/   Workbench design reference + build spec  ← start here for UI work
docs/ENGINE_BACKLOG.md   engine features the Workbench needs, with golden test values
```

## Run and test

```bash
pip install -e "engine[test]" && (cd engine && pytest)
pip install -r api/requirements.txt && (cd api && PYTHONPATH=.:../engine pytest)
cd api && PYTHONPATH=.:../engine uvicorn main:app --reload     # :8000, docs at /docs
cd web && npm install && npm run dev                            # :3000
cd web && npm run lint && npx tsc --noEmit && npm run build     # must pass before commit
```

## Non-negotiables

1. **No made-up content.** Every number, date, dignity and yoga shown must come from the
   engine or a documented classical rule. No placeholder astrology text, no invented
   interpretations. If something is not computed yet, show it as unavailable.
2. **Classical rules are cited in code.** Each rule table (dignities, friendships, aspects,
   karakas…) has a docstring naming the rule and its source (e.g. BPHS).
3. **Every setting is explicit and echoed.** Ayanamsha, node type, house system, sunrise
   convention, dasha year length — configurable, returned in responses, shown in the UI.
4. **Tests first for engine rules.** Each engine addition ships with pytest cases, including
   the golden values in `docs/ENGINE_BACKLOG.md`.
5. **Times:** engine works in UTC; the UI shows local time of the chart's place unless
   labelled. Event times (ingresses, period changes) are found to the minute, not by
   day-stepping.
6. **Accessibility:** real buttons/inputs, keyboard reachable, visible focus, text contrast
   ≥ 4.5:1 on the dark theme.

## Defaults

Lahiri (true, with nutation) · mean node · geocentric · whole-sign houses · upper-limb
sunrise with refraction · amanta month · dasha year 365.2425 days.
Without Swiss Ephemeris `.se1` files the Moshier ephemeris is used; responses say which.

## Status

- Engine v0.2: grahas, lagna/bhavas, 16 vargas, panchang, Vimshottari, JHora `.jhd`
  importer — 108 tests, independently reviewed.
- API: `/v1/chart`, `/v1/panchang`, `/v1/places`, `/v1/import/jhd` — 25 tests.
- `web/` pages are **v0 and will be replaced** by the Workbench (docs/design).
