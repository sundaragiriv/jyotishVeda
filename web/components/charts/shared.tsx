import { GRAHA_LABEL, GRAHA_ORDER, LabelScript, Placement, RASIS } from "@/lib/jyotish";

export interface ChartProps {
  lagnaRasi: number;          // 1-12
  placements: Placement[];
  script: LabelScript;
  title: string;              // e.g. "D9 · Navamsa"
  size?: number;              // max rendered width in px
}

export function dms(deg: number) {
  const d = Math.floor(deg);
  const m = Math.floor((deg - d) * 60);
  return `${d}°${String(m).padStart(2, "0")}′`;
}

/** Lagna first, then grahas in classical order. */
export function sortBodies(list: Placement[]) {
  const rank = (b: string) => (b === "Lagna" ? -1 : GRAHA_ORDER.indexOf(b));
  return [...list].sort((a, b) => rank(a.body) - rank(b.body));
}

/** Plain-language summary for screen readers. */
export function chartSummary(title: string, lagnaRasi: number, placements: Placement[]) {
  const parts = sortBodies(placements)
    .filter((p) => p.body !== "Lagna")
    .map((p) => `${p.body} in ${RASIS[p.rasi - 1]}${p.retrograde ? " (retrograde)" : ""}`);
  return `${title}. Lagna in ${RASIS[lagnaRasi - 1]}. ${parts.join(", ")}.`;
}

/** Labels of the bodies in one box, laid out in a small grid around (cx, cy). */
export function BodyLabels({
  bodies, cx, cy, cols, script, lineHeight = 19,
}: {
  bodies: Placement[]; cx: number; cy: number; cols: number; script: LabelScript; lineHeight?: number;
}) {
  const list = sortBodies(bodies);
  const rows = Math.ceil(list.length / cols);
  const colW = script === "sa" ? 30 : 28;
  return (
    <g>
      {list.map((p, i) => {
        const r = Math.floor(i / cols);
        const inRow = Math.min(cols, list.length - r * cols);
        const c = i % cols;
        const x = cx + (c - (inRow - 1) / 2) * colW;
        const y = cy + (r - (rows - 1) / 2) * lineHeight;
        const lbl = GRAHA_LABEL[p.body];
        const isLagna = p.body === "Lagna";
        return (
          <text
            key={p.body}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={script === "sa" ? 16 : 14.5}
            fontWeight={isLagna ? 700 : 600}
            fill={isLagna ? "var(--lagna)" : "var(--ink)"}
            fontFamily={script === "sa" ? "var(--font-deva)" : "var(--font-sans)"}
          >
            <title>
              {`${lbl.full}${p.degree !== undefined ? ` — ${dms(p.degree)} ${RASIS[p.rasi - 1]}` : ""}${p.retrograde ? " (retrograde)" : ""}`}
            </title>
            {script === "sa" ? lbl.sa : lbl.en}
            {p.retrograde && (
              <tspan fontSize={9} dy={-6} fill="var(--malefic)">R</tspan>
            )}
          </text>
        );
      })}
    </g>
  );
}
