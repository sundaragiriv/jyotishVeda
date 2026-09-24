# Engine backlog for the Workbench

Everything the Workbench shows must come from `engine/`. These are the additions it
needs, in build order. Each ships with pytest cases; the **golden values** below were
produced by the current engine for the sample chart and must be reproduced exactly.

**Sample chart:** 15 Aug 1990, 10:00 IST (04:30 UTC), Hyderabad 17.385 N, 78.4867 E,
Lahiri, mean node, whole-sign houses.

| Body | Longitude | Rasi | Nakshatra · pada | House |
|---|---|---|---|---|
| Lagna | 174.738° | Kanya 24°44′16″ | Chitra 1 | 1 |
| Surya | 118.375° | Karka 28°22′30″ | Ashlesha 4 | 11 |
| Chandra | 48.633° | Vrishabha 18°37′58″ | Rohini 3 | 9 |
| Mangala | 27.475° | Mesha 27°28′30″ | Krittika 1 | 8 |
| Budha | 145.430° | Simha 25°25′47″ | P.Phalguni 4 | 12 |
| Guru | 95.602° | Karka 05°36′08″ | Pushya 1 | 11 |
| Shukra | 97.817° | Karka 07°49′02″ | Pushya 2 | 11 |
| Shani (R) | 266.149° | Dhanu 26°08′57″ | P.Ashadha 4 | 4 |
| Rahu | 282.755° | Makara 12°45′17″ | Shravana 1 | 5 |
| Ketu | 102.755° | Karka 12°45′17″ | Pushya 3 | 11 |

---

## E1 · Sign dignity (any varga)

Rule (BPHS): exaltation Su Mesha, Mo Vrishabha, Ma Makara, Me Kanya, Ju Karka, Ve Meena,
Sa Tula; debilitation = 7th from exaltation. Own signs: Su Simha; Mo Karka; Ma Mesha,
Vrischika; Me Mithuna, Kanya; Ju Dhanu, Meena; Ve Vrishabha, Tula; Sa Makara, Kumbha.
Otherwise the natural relationship of the graha to the sign lord:

| Graha | Friends | Neutral | Enemies |
|---|---|---|---|
| Surya | Mo, Ma, Ju | Me | Ve, Sa |
| Chandra | Su, Me | Ma, Ju, Ve, Sa | — |
| Mangala | Su, Mo, Ju | Ve, Sa | Me |
| Budha | Su, Ve | Ma, Ju, Sa | Mo |
| Guru | Su, Mo, Ma | Sa | Me, Ve |
| Shukra | Me, Sa | Ma, Ju | Su, Mo |
| Shani | Me, Ve | Ju | Su, Mo, Ma |

Output codes `EX OW FR NE EN DB`. Rahu/Ketu: no dignity by default (setting, since
traditions differ). Moolatrikona is a later, D1-only refinement — verify degree ranges
against BPHS before adding.

**Golden (D1):** Su FR, Mo EX, Ma OW, Me FR, Ju EX, Ve EN, Sa NE.
**Golden (D9):** Su FR (Meena), Mo FR (Mithuna), Ma FR (Dhanu), Me NE (Vrischika),
Ju FR (Simha), Ve **DB** (Kanya), Sa EN (Vrischika).

## E2 · Varga dignity matrix

`graha × 16 vargas → (rasi, dignity)` plus counts. **Golden rows:**

```
Guru   D1..D60: Ka:EX Ka:EX Ka:EX Ka:EX Ku:NE Si:FR Me:FR Kn:EN Mi:EN Ka:EX Vc:FR Mi:EN Kn:EN Vs:EN Dh:OW Mi:EN   → Ex/Own 6, Db 0
Shukra D1..D60: Ka:EN Ka:EN Ka:EN Tu:OW Ku:FR Kn:DB Vs:OW Tu:OW Si:EN Kn:DB Mk:FR Si:EN Kn:DB Si:EN Mn:EX Tu:OW   → Ex/Own 5, Db 3
```
(column order D1 D2 D3 D4 D7 D9 D10 D12 D16 D20 D24 D27 D30 D40 D45 D60)

**Vargottama** (same rasi in D1 and D9): none in the sample chart.

## E3 · House lordships

Whole-sign from lagna. **Golden:** 1 Me · 2 Ve · 3 Ma · 4 Ju · 5 Sa · 6 Sa · 7 Ju · 8 Ma ·
9 Ve · 10 Me · 11 Mo · 12 Su. Lord placements: Me→12, Ve→11, Ma→8, Ju→11, Sa→4,
Mo→9, Su→11.

## E4 · Graha drishti (Parashari aspects)

All grahas aspect the 7th from themselves; Mangala also 4th and 8th; Guru 5th and 9th;
Shani 3rd and 10th. Rahu/Ketu aspects: off by default (setting; traditions differ).
**Golden:** 10th house (Mithuna) is aspected only by Shani (from the 4th, 7th aspect).
Shani aspects houses 6, 10, 1. Guru aspects 3, 5, 7. Mangala aspects 11, 2, 3.

## E5 · Parivartana (sign exchange)

Two grahas each in the other's sign. Classify: **dainya** if either lord rules 6, 8 or 12;
else **khala** if either rules 3; else **maha**.
**Golden:** exactly one — Shukra (lord 2, 9) in Karka ↔ Chandra (lord 11) in Vrishabha,
houses 11 ↔ 9 → maha parivartana. (Shukra also rules 2: still maha.)

## E6 · Combustion (asta)

Angular distance from Surya within: Mo 12°, Ma 17°, Me 14° (12° if retrograde),
Ju 11°, Ve 10° (8° if retrograde), Sa 15°. Verify orbs against the source before release
and make them a setting. **Golden:** none combust in the sample chart.

## E7 · Chara karakas (Jaimini)

Rank Su–Sa by degrees within their sign, descending: AK, AmK, BK, MK, PK, GK, DK
(7-karaka scheme, default). 8-karaka scheme (adds Rahu, counted as 30° − degree) as a setting.
**Golden (7-scheme):** AK Surya · AmK Mangala · BK Shani · MK Budha · PK Chandra ·
GK Shukra · DK Guru.

## E8 · Transits and ingress times

- Positions for any time-cursor instant (reuse `compute_graha_positions`).
- `find_ingresses(graha, start, end)` → every sign change, found by bisection **to the
  minute** (day-stepping is not acceptable: it was 1–2 days off in the first design pass).
- Sade Sati: Shani in the 12th, 1st or 2nd sign from natal Chandra, with phases and
  retrograde re-entries.

**Golden ingresses (UTC):**
- Guru → Karka 2026-06-01 20:20 · Guru → Simha 2026-10-31 06:32
- Rahu → Makara 2026-12-05 17:02 (returns to its natal sign)
- Shani → Mesha 2027-06-02 23:58 → **Sade Sati begins** (natal Chandra in Vrishabha);
  Shani back to Meena 2027-10-22 (±1 day, confirm by bisection), re-enters Mesha 2028-02-25 (±1 day)

## E9 · Dasha at the time cursor

Already available (`active_periods`, depth 3). **Golden at 2026-09-24:** Guru MD
(2019-02-23 → 2035-02-23) › Ketu AD (2026-01-29 → 2027-01-05) › Guru PD (2026-08-11 →
2026-09-25). Next PD: Shani 2026-09-25; Budha PD 2026-11-18 → 2027-01-05.

## E10 · Bhava lens

`bhava_lens(chart, house)` → sign, occupants, lord and its placement/dignity, aspects
received (E4), house karakas, the same house in the relevant varga (10th → D10, 7th → D9,
4th → D4, 5th → D7…), dasha periods of the lord (past/next), and slow-planet transits over
the house at the cursor.
House karakas (standard list, verify against BPHS): 1 Su · 2 Ju · 3 Ma · 4 Mo, Me ·
5 Ju · 6 Sa, Ma · 7 Ve · 8 Sa · 9 Ju, Su · 10 Su, Me, Ju, Sa · 11 Ju · 12 Sa.
**Golden (10th):** Mithuna, empty; lord Budha in 12th (Simha, FR), also lagna lord;
aspected by Shani; D10 lagna Makara (with Mangala, Rahu), D10 10th Tula empty, its lord
Shukra in Vrishabha (own sign), Budha in D10 Mesha with Guru.

## E11 · Synthesis facts (no LLM yet)

A rule engine that emits **facts with evidence**, e.g.
`{id: "parivartana", kind: "maha", grahas: ["Shukra","Chandra"], houses: [11, 9], evidence: [...]}`.
The UI renders facts; an LLM may later rephrase them, but never adds claims without
evidence. Start with: parivartana, exalted/debilitated grahas with houses, lagna-lord
placement, varga weakness (debilitated in D9), vargottama, upcoming ingresses and
Sade Sati.

## API additions

`POST /v1/chart` gains `dignities`, `lordships`, `aspects`, `karakas`, `yogas.parivartana`,
`combust`, `vargottama`, `varga_matrix`. New: `GET /v1/transits?at=…`,
`GET /v1/ingresses?from=…&to=…&grahas=…`, `POST /v1/bhava-lens`, `POST /v1/synthesis`.
Keep `/v1/chart` fast (< 150 ms): heavy items (ingress search) are separate endpoints.
