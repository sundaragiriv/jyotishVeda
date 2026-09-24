# First prompt for Claude Code (paste as-is)

Read `CLAUDE.md`, `docs/design/WORKBENCH_SPEC.md`, `docs/ENGINE_BACKLOG.md`, and look at
`docs/design/Workbench.dc.html` (layout and sample data are in the file).

Goal: build the Jyotisha Veda Workbench in `web/` exactly as specified, backed by the
engine. Work in this order, committing after each step with tests passing:

1. **Engine E1–E7** (dignity, varga matrix, lordships, aspects, parivartana, combustion,
   chara karakas) in new modules under `engine/`, each with pytest cases that reproduce
   the golden values in ENGINE_BACKLOG.md. Cite the classical rule in each docstring.
2. **Engine E8–E11** (ingress finder to the minute, Sade Sati, dasha at cursor, bhava lens,
   synthesis facts) with golden-value tests.
3. **API**: extend `/v1/chart` and add `/v1/transits`, `/v1/ingresses`, `/v1/bhava-lens`,
   `/v1/synthesis`, with tests. Keep `/v1/chart` under 150 ms.
4. **Web**: replace the v0 pages with the Workbench. Build panels in this order:
   charts → matrix → table → ribbon → lens → synthesis → command bar. Add linked graha
   selection and the time cursor as shared state (one store, no prop drilling).
5. Verify against the spec's acceptance criteria: run the app, load the sample chart
   (15 Aug 1990 10:00 IST, Hyderabad), compare every value to the golden values, take
   screenshots at 1920×1080 and 1440×900, fix what differs.

Rules: no invented astrology content; anything not computed shows "Not available yet".
Ask me before changing a classical rule or a default setting. Before step 4, show me a
plan for the frontend state and component structure.
