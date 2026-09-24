"use client";

import { useId } from "react";
import { ChartResponse } from "@/lib/api";
import { LabelScript, VARGAS, vargaPlacements } from "@/lib/jyotish";
import NorthIndianChart from "./charts/NorthIndianChart";
import SouthIndianChart from "./charts/SouthIndianChart";

export type ChartStyle = "south" | "north";

export default function ChartPanel({
  chart, varga, onVarga, style, script,
}: {
  chart: ChartResponse; varga: number; onVarga: (n: number) => void; style: ChartStyle; script: LabelScript;
}) {
  const id = useId();
  const meta = VARGAS.find((v) => v.n === varga)!;
  const { lagnaRasi, placements } = vargaPlacements(chart, varga);
  const title = `D${varga} · ${meta.name}`;
  const Chart = style === "south" ? SouthIndianChart : NorthIndianChart;

  return (
    <figure className="card flex flex-col items-center gap-3 p-4">
      <figcaption className="flex w-full items-center justify-between gap-2">
        <div>
          <label htmlFor={id} className="sr-only">Divisional chart</label>
          <select id={id} value={varga} onChange={(e) => onVarga(Number(e.target.value))}
            className="field !min-h-[40px] !w-auto !py-1.5 font-medium">
            {VARGAS.map((v) => (
              <option key={v.n} value={v.n}>D{v.n} · {v.name}</option>
            ))}
          </select>
        </div>
        <span className="text-right text-xs text-ink-3">{meta.area}</span>
      </figcaption>
      <Chart lagnaRasi={lagnaRasi} placements={placements} script={script} title={title} />
    </figure>
  );
}
