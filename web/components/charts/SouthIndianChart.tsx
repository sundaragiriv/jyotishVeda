import { RASIS, RASI_SHORT } from "@/lib/jyotish";
import { BodyLabels, ChartProps, chartSummary } from "./shared";

/**
 * South Indian chart: rasis are FIXED in the outer ring of a 4×4 grid,
 * Meena at top-left running clockwise; the Lagna is marked with a diagonal.
 */
const CELL: Record<number, [number, number]> = {
  12: [0, 0], 1: [1, 0], 2: [2, 0], 3: [3, 0],
  11: [0, 1], 4: [3, 1],
  10: [0, 2], 5: [3, 2],
  9: [0, 3], 8: [1, 3], 7: [2, 3], 6: [3, 3],
};
const S = 100;

export default function SouthIndianChart({ lagnaRasi, placements, script, title, size = 440 }: ChartProps) {
  return (
    <svg viewBox="-2 -2 404 404" role="img" aria-label={chartSummary(title, lagnaRasi, placements)}
      style={{ width: "100%", maxWidth: size, height: "auto" }}>
      <rect x={0} y={0} width={400} height={400} fill="var(--chart-fill)" stroke="var(--chart-line)" strokeWidth={1.5} rx={6} />
      {Object.entries(CELL).map(([rasiStr, [c, r]]) => {
        const rasi = Number(rasiStr);
        const x = c * S, y = r * S;
        const bodies = placements.filter((p) => p.rasi === rasi);
        const isLagna = rasi === lagnaRasi;
        return (
          <g key={rasi}>
            <rect x={x} y={y} width={S} height={S} fill={isLagna ? "var(--accent-soft)" : "none"}
              stroke="var(--chart-line)" strokeWidth={1} />
            {isLagna && (
              <line x1={x} y1={y + 26} x2={x + 26} y2={y} stroke="var(--lagna)" strokeWidth={1.6} />
            )}
            <text x={x + S - 6} y={y + S - 7} textAnchor="end" fontSize={10} fill="var(--ink-3)">
              <title>{RASIS[rasi - 1]}</title>
              {RASI_SHORT[rasi - 1]}
            </text>
            <BodyLabels bodies={bodies} cx={x + S / 2} cy={y + S / 2 - 4} cols={3} script={script} />
          </g>
        );
      })}
      <text x={200} y={192} textAnchor="middle" fontFamily="var(--font-display)" fontSize={26}
        fontWeight={600} fill="var(--ink)">{title.split(" · ")[1] ?? title}</text>
      <text x={200} y={218} textAnchor="middle" fontSize={12} fill="var(--ink-3)" letterSpacing={1.5}>
        {title.split(" · ")[0]}
      </text>
    </svg>
  );
}
