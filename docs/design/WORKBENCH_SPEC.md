# Jyotisha Veda Workbench — build spec v1

Visual reference: `Workbench.dc.html` (same folder). It is a design-canvas file: the markup
shows layout and styling; the `<script>` block at the bottom holds the exact sample data.
Treat it as the look to match, not code to copy.

## Who and why

Practising astrologers and serious students. They read a chart by moving between the rasi
chart, divisional charts, strengths, one house at a time, and time periods. Jagannatha Hora
spreads this across many windows; the Workbench puts it on one screen, linked.
**Density is a feature.** Desktop-first (1440–2560 px wide). Tablet later; phone is ChitraGupta's job.

## Layout (1920 × 1080 reference)

```
┌ Top bar 48 ─ app mark · chart tabs · ⌘K command bar · settings chip · time-cursor chip ┐
├ Charts 430 ┬ Matrix + table 700 ┬ Bhava lens 360 ┬ Synthesis 370 ┤  height ≈ 788
├────────────┴────────────────────┴────────────────┴───────────────┤
└ Time ribbon (full width) ≈ 220                                    ┘
```
Panels are resizable and collapsible (persist per user). At < 1600 px the Synthesis panel
docks under the Bhava lens as a tab.

## Panels

**1. Charts** — D1 (South Indian, dense) plus two mini charts (defaults D9, D10; either can
be switched to any of the 16 vargas). South/North toggle; North uses the SVG renderer in
`web/components/charts/`.
Each D1 body line shows: dignity dot · abbreviation (gem colour) · degree °′ · nakshatra
abbreviation + pada · retrograde marker. Each cell shows the rasi name and house number;
lagna and the lens house are tinted.

**2. Varga dignity matrix** — rows Lagna + 9 grahas, columns the 16 vargas; each cell shows
the rasi (2 letters) on a dignity-tinted background; last column Ex+Own / Db counts.
Hovering a cell shows `D9 Kanya · Debilitated`. Footer line: vargottama grahas and notable
patterns, generated from engine facts only. Data: E1, E2.

**3. Graha details table** — Graha · longitude (rasi d°m′s″) · nakshatra · pada · nakshatra
lord · house · houses ruled · dignity · chara karaka · speed °/day (negative = retrograde,
coloured). Data: existing + E1, E3, E7.

**4. Bhava lens** — 12 house tabs; content for the chosen house: rasi chart facts, the
relevant varga, timing (lord's periods, next one highlighted), transits over the house at
the cursor. Actions: Pin to report · Open varga full · Compare with another house.
Data: E10.

**5. Synthesis** — list of facts from E11, each with a title, one plain sentence and
evidence chips (graha · role · place). Chips select the graha everywhere. "Ask about this
chart" input is present but disabled until the AI layer exists (tooltip says so).
No text that is not backed by a fact.

**6. Time ribbon** — tracks on one time axis: Mahadasha, Antardasha, Pratyantar, Shani
transit, Guru transit, Rahu transit, Sade Sati. Default window: 3 years around today; zoom
with ⌘/ctrl + scroll (days → decades). A draggable **time cursor** (default now) drives:
transit positions, the dasha chain in the top bar chip, lens "transits", Synthesis "ahead".
Data: E8, E9.

## Interactions (the parts JHora cannot do)

- **Linked selection.** Selecting a graha (click in any panel, or keys `1`–`9` for
  Su…Ke) highlights it in every panel at once: chart line, matrix row, table row,
  mini-chart underline, synthesis chips, ribbon periods ruled by it. `Esc` clears.
- **Time cursor.** Drag on the ribbon, or `[` / `]` step by day, `{` / `}` by month,
  `T` = today. All time-dependent panels update without a full reload (debounce 100 ms).
- **Command bar (⌘K / ctrl-K).** Fuzzy commands: `D10`, `navamsa`, `10th`, `lord of 10`,
  `shani`, `2027-06`, `sade sati`, `open vivekananda`, `settings: true node`.
- **Chart tabs.** Several charts open at once; `⌘1…9` switches.
- Every control reachable by keyboard; shortcut list on `?`.

## Visual system

- Theme: dark (reference) first; light theme later with the same tokens.
- Surfaces: page `#090A1F`, panel `#11133A`, inset `#0D0F2B`, line `#262A5C`/`#3A3F86`.
- Text: primary `#E9E3D6`, secondary `#B9B3C9`, muted `#9A94B3` (≥ 4.5:1 on panel).
- Accent: saffron `#F2A33A` (selection, lagna), gold `#F4C542` (exalted, current period).
- Graha gem colours (Navaratna): Su `#E23D57` · Mo `#EDE6D6` · Ma `#F2704F` · Me `#2FBF8A` ·
  Ju `#F4C542` · Ve `#D6E6FF` · Sa `#7F97F5` (text) / `#4B6BE8` (fill) · Ra `#CB7A3E` · Ke `#A7B36B`.
- Dignity: EX gold, OW green, FR pale green, NE grey, EN salmon, DB red (tints in the reference).
- Type: Hind (UI, 12–14 px), JetBrains Mono (degrees, tables), Fraunces (titles, sparingly),
  Tiro Devanagari Sanskrit (mark). Self-host via @fontsource (Google Fonts is not reachable
  in every build environment).
- Density: 12.5–13 px base, 24–26 px rows, 12 px panel gaps, no decorative imagery.

## States

Loading: skeleton panels in place (no layout shift). Engine error: panel-level message
with the API's detail. Not yet computed (e.g. Shadbala): panel says "Not available yet",
never sample numbers.

## Acceptance criteria (v1)

1. With the sample chart loaded, every value in the reference renders from the API and
   matches `docs/ENGINE_BACKLOG.md` golden values.
2. Selecting a graha in any panel highlights it in all panels within one frame.
3. Moving the time cursor updates transit and dasha displays; the dasha chip shows
   Guru › Ketu › Guru at 2026-09-24 and Guru › Ketu › Shani at 2026-09-26.
4. ⌘K opens the command bar; `D10` switches a mini chart; `10th` sets the lens.
5. Lighthouse accessibility ≥ 95; all actions keyboard-reachable; no text below 4.5:1.
6. Chart render < 150 ms after API response on a mid-range laptop.
7. `npm run lint`, `tsc`, `build` and all engine/API tests pass.

## Out of scope for v1

Shadbala, Ashtakavarga, yogas beyond parivartana, AI text, PDF reports, light theme,
mobile layout, user accounts.
