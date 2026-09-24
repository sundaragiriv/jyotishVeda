import { RASIS } from "@/lib/jyotish";
import { BodyLabels, ChartProps, chartSummary } from "./shared";

/**
 * North Indian chart: HOUSES are fixed (1st house = top centre diamond,
 * counting counter-clockwise); the rasi number in each house rotates with
 * the Lagna.
 */
type Pt = [number, number];
const HOUSES: Pt[][] = [
  [[200, 0], [300, 100], [200, 200], [100, 100]],   // 1
  [[0, 0], [200, 0], [100, 100]],                   // 2
  [[0, 0], [100, 100], [0, 200]],                   // 3
  [[0, 200], [100, 100], [200, 200], [100, 300]],   // 4
  [[0, 200], [100, 300], [0, 400]],                 // 5
  [[0, 400], [100, 300], [200, 400]],               // 6
  [[200, 400], [100, 300], [200, 200], [300, 300]], // 7
  [[200, 400], [300, 300], [400, 400]],             // 8
  [[400, 400], [300, 300], [400, 200]],             // 9
  [[400, 200], [300, 300], [200, 200], [300, 100]], // 10
  [[400, 200], [300, 100], [400, 0]],               // 11
  [[400, 0], [300, 100], [200, 0]],                 // 12
];
const SIDE_TRIANGLES = new Set([3, 5, 9, 11]);

function centroid(poly: Pt[]): Pt {
  const n = poly.length;
  return [poly.reduce((s, p) => s + p[0], 0) / n, poly.reduce((s, p) => s + p[1], 0) / n];
}

/** Vertex closest to the chart centre: where the rasi number sits. */
function innerVertex(poly: Pt[]): Pt {
  return poly.reduce((best, p) =>
    Math.hypot(p[0] - 200, p[1] - 200) < Math.hypot(best[0] - 200, best[1] - 200) ? p : best);
}

export default function NorthIndianChart({ lagnaRasi, placements, script, title, size = 440 }: ChartProps) {
  return (
    <svg viewBox="-2 -2 404 404" role="img" aria-label={chartSummary(title, lagnaRasi, placements)}
      style={{ width: "100%", maxWidth: size, height: "auto" }}>
      <rect x={0} y={0} width={400} height={400} fill="var(--chart-fill)" stroke="var(--chart-line)" strokeWidth={1.5} rx={6} />
      {HOUSES.map((poly, i) => {
        const house = i + 1;
        const rasi = ((lagnaRasi - 1 + i) % 12) + 1;
        const [cx, cy] = centroid(poly);
        const [ix, iy] = innerVertex(poly);
        const numX = ix + 0.3 * (cx - ix);
        const numY = iy + 0.3 * (cy - iy);
        const bodies = placements.filter((p) => p.rasi === rasi);
        const isDiamond = poly.length === 4;
        // body block sits between the centroid and the outer edge
        const bx = isDiamond ? cx : cx + 0.15 * (cx - ix);
        const by = isDiamond ? cy - 12 : cy + 0.15 * (cy - iy);
        return (
          <g key={house}>
            <polygon points={poly.map((p) => p.join(",")).join(" ")}
              fill={house === 1 ? "var(--accent-soft)" : "none"}
              stroke="var(--chart-line)" strokeWidth={1} strokeLinejoin="round" />
            <text x={numX} y={numY} textAnchor="middle" dominantBaseline="central" fontSize={11}
              fill={house === 1 ? "var(--lagna)" : "var(--ink-3)"} fontWeight={house === 1 ? 700 : 400}>
              <title>{`House ${house}: ${RASIS[rasi - 1]}`}</title>
              {rasi}
            </text>
            <BodyLabels bodies={bodies.filter((b) => b.body !== "Lagna")} cx={bx} cy={by}
              cols={SIDE_TRIANGLES.has(house) ? 2 : 3} script={script} lineHeight={18} />
          </g>
        );
      })}
    </svg>
  );
}
