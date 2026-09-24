import { ChartResponse } from "@/lib/api";
import { GRAHA_LABEL } from "@/lib/jyotish";

export default function GrahaTable({ chart }: { chart: ChartResponse }) {
  const rows = [
    { key: "Lagna", name: "Lagna", rasi: chart.lagna.rasi, deg: chart.lagna.degree_in_rasi_dms,
      nak: chart.lagna.nakshatra, pada: chart.lagna.pada, lord: "", house: 1, retro: false },
    ...chart.grahas.map((g) => ({
      key: g.graha, name: g.graha, rasi: g.rasi, deg: g.degree_in_rasi_dms, nak: g.nakshatra,
      pada: g.pada, lord: g.nakshatra_lord, house: g.house, retro: g.retrograde && g.graha !== "Rahu" && g.graha !== "Ketu",
    })),
  ];
  return (
    <section className="card overflow-hidden" aria-labelledby="gt-h">
      <h2 id="gt-h" className="px-5 pt-4 font-display text-xl font-semibold">Graha positions</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <caption className="sr-only">Sidereal positions of the Lagna and nine grahas</caption>
          <thead>
            <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-ink-3">
              <th scope="col" className="px-5 py-2 font-medium">Graha</th>
              <th scope="col" className="px-3 py-2 font-medium">Rasi</th>
              <th scope="col" className="px-3 py-2 text-right font-medium">Degree</th>
              <th scope="col" className="px-3 py-2 font-medium">Nakshatra · Pada</th>
              <th scope="col" className="px-3 py-2 font-medium">Nak. lord</th>
              <th scope="col" className="px-5 py-2 text-right font-medium">House</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-b border-line/60 last:border-0">
                <th scope="row" className="px-5 py-2 text-left font-medium">
                  <span className="mr-2 inline-block w-8 font-deva text-accent" aria-hidden>{GRAHA_LABEL[r.key].sa}</span>
                  {r.name}
                  {r.retro && <span className="ml-1.5 rounded bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold text-ink-2" title="Retrograde (vakri)">R</span>}
                </th>
                <td className="px-3 py-2">{r.rasi}</td>
                <td className="px-3 py-2 text-right tabular-nums">{r.deg.replace(/\.\d+"$/, '"')}</td>
                <td className="px-3 py-2">{r.nak} · {r.pada}</td>
                <td className="px-3 py-2 text-ink-2">{r.lord}</td>
                <td className="px-5 py-2 text-right tabular-nums">{r.house}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
