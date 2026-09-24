"use client";

import { useState } from "react";
import BirthForm, { BirthData } from "@/components/BirthForm";
import ChartPanel, { ChartStyle } from "@/components/ChartPanel";
import DashaTimeline from "@/components/DashaTimeline";
import GrahaTable from "@/components/GrahaTable";
import { ApiError, ChartResponse, fetchChart } from "@/lib/api";
import { LabelScript } from "@/lib/jyotish";

export default function ChartPage() {
  const [chart, setChart] = useState<ChartResponse | null>(null);
  const [birth, setBirth] = useState<BirthData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [style, setStyle] = useState<ChartStyle>("south");
  const [script, setScript] = useState<LabelScript>("en");
  const [left, setLeft] = useState(1);
  const [right, setRight] = useState(9);

  // Set when the local time falls in a daylight-saving change: the user picks the offset
  const [dstChoice, setDstChoice] = useState<{ birth: BirthData; kind: string; offsets: number[] } | null>(null);

  const cast = async (b: BirthData, offsetMinutes?: number) => {
    setBusy(true);
    setError("");
    setDstChoice(null);
    try {
      const time = b.time.length === 5 ? `${b.time}:00` : b.time;
      const where = offsetMinutes === undefined
        ? { tz: b.place.timezone }
        : { utc_offset_minutes: offsetMinutes };
      const c = await fetchChart(
        { local_datetime: `${b.date}T${time}`, ...where,
          latitude: b.place.latitude, longitude: b.place.longitude },
        b.options,
      );
      setChart(c);
      setBirth(b);
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Something went wrong while calculating.";
      const m = msg.match(/(does not exist|occurs twice).*one of \[(-?\d+), (-?\d+)\]/);
      if (m) setDstChoice({ birth: b, kind: m[1], offsets: [Number(m[2]), Number(m[3])] });
      else setError(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid gap-6 pt-2 lg:grid-cols-[340px_1fr]">
      <aside className="lg:sticky lg:top-4 lg:self-start">
        <BirthForm onSubmit={(b) => cast(b)} busy={busy} />
      </aside>

      <div className="min-w-0 space-y-6" aria-live="polite" aria-busy={busy}>
        {error && (
          <div role="alert" className="card border-danger/40 p-4 text-sm text-danger">{error}</div>
        )}

        {dstChoice && (
          <div role="alert" className="card space-y-3 p-5">
            <p className="font-medium">
              {dstChoice.kind === "does not exist"
                ? `Clocks in ${dstChoice.birth.place.name} jumped forward that night, so ${dstChoice.birth.time.slice(0, 5)} never showed on the clock.`
                : `Clocks in ${dstChoice.birth.place.name} went back that night, so ${dstChoice.birth.time.slice(0, 5)} happened twice.`}
            </p>
            <p className="text-sm text-ink-2">Which clock time was recorded? If unsure, check the birth certificate.</p>
            <div className="flex flex-wrap gap-2">
              {dstChoice.offsets.map((o) => (
                <button key={o} className="btn btn-ghost" onClick={() => cast(dstChoice.birth, o)}>
                  {o === Math.max(...dstChoice.offsets) ? "Daylight time" : "Standard time"} (UTC{o < 0 ? "−" : "+"}{fmtOffset(Math.abs(o))})
                </button>
              ))}
            </div>
          </div>
        )}

        {!chart && !error && !dstChoice && <EmptyState />}

        {chart && birth && (
          <>
            <header className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 className="font-display text-3xl font-semibold sm:text-4xl">
                  {birth.name || "Birth chart"}
                </h1>
                <p className="mt-1 text-sm text-ink-2">
                  {new Date(`${birth.date}T12:00:00`).toLocaleDateString("en-IN", { dateStyle: "long" })}
                  {" · "}{birth.time.slice(0, 5)} local · {birth.place.name}
                </p>
                <p className="mt-0.5 text-xs text-ink-3">
                  {chart.settings.ayanamsha} ayanamsha {chart.settings.ayanamsha_dms.replace(/\.\d+"$/, '"')} · {chart.settings.node} node · UTC {chart.input.utc.slice(0, 16).replace("T", " ")}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <div className="seg" role="group" aria-label="Chart style">
                  <button aria-pressed={style === "south"} onClick={() => setStyle("south")}>South</button>
                  <button aria-pressed={style === "north"} onClick={() => setStyle("north")}>North</button>
                </div>
                <div className="seg" role="group" aria-label="Graha labels">
                  <button aria-pressed={script === "en"} onClick={() => setScript("en")}>Su Mo</button>
                  <button aria-pressed={script === "sa"} onClick={() => setScript("sa")} className="font-deva">सू चं</button>
                </div>
              </div>
            </header>

            <div className="grid gap-6 md:grid-cols-2">
              <ChartPanel chart={chart} varga={left} onVarga={setLeft} style={style} script={script} />
              <ChartPanel chart={chart} varga={right} onVarga={setRight} style={style} script={script} />
            </div>

            <GrahaTable chart={chart} />
            <DashaTimeline chart={chart} />
          </>
        )}
      </div>
    </div>
  );
}

function fmtOffset(min: number) {
  return `${Math.floor(min / 60)}${min % 60 ? `:${String(min % 60).padStart(2, "0")}` : ""}`;
}

function EmptyState() {
  return (
    <div className="card grid min-h-[420px] place-items-center p-8 text-center">
      <div className="max-w-md">
        <p className="font-deva text-4xl text-accent" aria-hidden>ॐ</p>
        <h1 className="mt-3 font-display text-3xl font-semibold">Cast a birth chart</h1>
        <p className="mt-2 text-ink-2">
          Enter the date, time and place of birth. You&apos;ll get the Rasi and Navamsa charts,
          all sixteen divisional charts, graha positions and the Vimshottari dasha.
        </p>
        <p className="mt-4 text-sm text-ink-3">No birth data handy? Use “Try an example”.</p>
      </div>
    </div>
  );
}
