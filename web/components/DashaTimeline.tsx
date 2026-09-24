"use client";

import { useMemo, useState } from "react";
import { ChartResponse } from "@/lib/api";
import { fmtDate } from "@/lib/jyotish";

// Text colour chosen per bar for contrast: dark hues get light text
const DARK_HUES = new Set(["Mangala", "Rahu", "Shani", "Ketu"]);

const LORD_HUE: Record<string, string> = {
  Ketu: "#8b6f5a", Shukra: "#c9a3c7", Surya: "#e0913a", Chandra: "#b8c4d6", Mangala: "#c9553f",
  Rahu: "#6f7a8c", Guru: "#e3b94a", Shani: "#5a6b9c", Budha: "#6fa77f",
};

export default function DashaTimeline({ chart }: { chart: ChartResponse }) {
  const { periods, current, balance_at_birth, moon_nakshatra } = chart.dasha;
  const birth = new Date(chart.input.utc).getTime();
  const [now] = useState(() => Date.now());
  const t0 = new Date(periods[0].start).getTime();
  const t1 = new Date(periods[periods.length - 1].end).getTime();
  const pct = (t: number) => ((t - t0) / (t1 - t0)) * 100;

  const currentMd = current[0]?.lord;
  const currentAd = current[1];
  const [selected, setSelected] = useState<string>(currentMd ?? periods[0].lord);
  const md = useMemo(() => periods.find((p) => p.lord === selected) ?? periods[0], [periods, selected]);

  return (
    <section className="card p-5" aria-labelledby="dt-h">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="dt-h" className="font-display text-xl font-semibold">Vimshottari dasha</h2>
        <p className="text-sm text-ink-2">
          Moon in {moon_nakshatra} · {balance_at_birth.lord} balance {balance_at_birth.years.toFixed(2)} yrs at birth
        </p>
      </div>

      {current.length > 0 && (
        <p className="mt-3 text-sm">
          <span className="text-ink-3">Running now: </span>
          <strong>{current.map((c) => c.lord).join(" › ")}</strong>
          {currentAd && <span className="text-ink-2"> (until {fmtDate(currentAd.end)})</span>}
        </p>
      )}

      {/* Mahadasha strip across the 120-year cycle */}
      <div className="relative mt-4" role="group" aria-label="Mahadashas; select one to see its antardashas">
        <div className="flex h-12 overflow-hidden rounded-lg border border-line">
          {periods.map((p) => {
            const w = pct(new Date(p.end).getTime()) - pct(new Date(p.start).getTime());
            const on = p.lord === selected;
            return (
              <button
                key={p.start}
                onClick={() => setSelected(p.lord)}
                aria-pressed={on}
                aria-label={`${p.lord} mahadasha, ${fmtDate(p.start)} to ${fmtDate(p.end)}`}
                title={`${p.lord}: ${fmtDate(p.start)} – ${fmtDate(p.end)}`}
                style={{ width: `${w}%`, background: LORD_HUE[p.lord] }}
                className={`relative min-w-0 border-r border-white/50 text-[11px] last:border-0 ${DARK_HUES.has(p.lord) ? "text-white" : "text-black/85"} ${on ? "font-bold ring-2 ring-inset ring-[var(--ink)]" : "font-medium"}`}
              >
                <span className="block truncate px-1">{w > 5 ? p.lord : p.lord.slice(0, 2)}</span>
              </button>
            );
          })}
        </div>
        {[{ t: birth, label: "Birth" }, { t: now, label: "Today" }].map((m) =>
          m.t > t0 && m.t < t1 ? (
            <div key={m.label} className="pointer-events-none absolute top-12" style={{ left: `${pct(m.t)}%` }} aria-hidden>
              <div className="h-2 w-px bg-[var(--ink)]" />
              <span className="absolute -translate-x-1/2 whitespace-nowrap text-[10px] font-medium text-ink-2">▲ {m.label}</span>
            </div>
          ) : null,
        )}
      </div>

      <h3 className="mt-8 text-sm font-semibold">
        {md.lord} mahadasha <span className="font-normal text-ink-2">· {fmtDate(md.start)} – {fmtDate(md.end)}</span>
      </h3>
      <ol className="mt-2 grid gap-1 sm:grid-cols-3">
        {md.periods?.map((ad) => {
          const running = currentAd && ad.start === currentAd.start;
          const past = new Date(ad.end).getTime() < now;
          return (
            <li key={ad.start}
              className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm ${running ? "bg-accent-soft font-semibold" : ""} ${past && !running ? "text-ink-3" : ""}`}>
              <span className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: LORD_HUE[ad.lord] }} aria-hidden />
                {md.lord}–{ad.lord}
                {running && <span className="sr-only">(running now)</span>}
              </span>
              <span className="tabular-nums text-xs">{fmtDate(ad.start, { month: "short", year: "numeric" })}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
