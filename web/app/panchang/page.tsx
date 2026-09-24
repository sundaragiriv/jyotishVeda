"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import PlaceSearch from "@/components/PlaceSearch";
import { ApiError, PanchangResponse, Place, Span, fetchPanchang } from "@/lib/api";
import { dayTag, fmtLocalTime } from "@/lib/jyotish";

const DEFAULT_PLACE: Place = {
  id: 1269843, name: "Hyderabad", region: "IN", country: "India",
  latitude: 17.38405, longitude: 78.45636, timezone: "Asia/Kolkata", population: 6993262,
};
const STORE_KEY = "jv-panchang-place";

function todayIn(tz: string) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: tz }).format(new Date()); // yyyy-mm-dd
}

function initialPlace(): Place {
  try {
    const saved = localStorage.getItem(STORE_KEY);
    if (saved) return JSON.parse(saved) as Place;
  } catch { /* storage unavailable or corrupt: use the default */ }
  return DEFAULT_PLACE;
}

type Result = { key: string; data?: PanchangResponse; error?: string };

// Rendered only in the browser (see page export below), so the saved place
// can be read during the first render without a hydration mismatch.
function PanchangApp() {
  const [place, setPlace] = useState<Place>(initialPlace);
  const [date, setDate] = useState(() => todayIn(initialPlace().timezone));
  const [result, setResult] = useState<Result | null>(null);

  const key = `${place.latitude},${place.longitude},${place.timezone}|${date}`;
  const busy = result?.key !== key;

  useEffect(() => {
    let cancelled = false;
    fetchPanchang({ date, latitude: place.latitude, longitude: place.longitude, tz: place.timezone })
      .then((data) => { if (!cancelled) setResult({ key, data }); })
      .catch((e) => {
        if (!cancelled) setResult({ key, error: e instanceof ApiError ? e.message : "Could not calculate the panchang." });
      });
    return () => { cancelled = true; };
  }, [key, date, place]);

  const choosePlace = (p: Place | null) => {
    if (!p) return;
    setPlace(p);
    try { localStorage.setItem(STORE_KEY, JSON.stringify(p)); } catch { /* ignore */ }
  };

  const shiftDay = (n: number) => {
    const d = new Date(`${date}T12:00:00Z`);
    d.setUTCDate(d.getUTCDate() + n);
    setDate(d.toISOString().slice(0, 10));
  };

  const shown = result?.data;
  return (
    <div className="space-y-6 pt-2">
      <section className="card grid gap-4 p-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
        <div className="min-w-0"><PlaceSearch value={place} onChange={choosePlace} label="Place" /></div>
        <div className="min-w-0">
          <label htmlFor="pc-date" className="label">Date</label>
          <div className="flex flex-wrap gap-2">
            <button className="btn btn-ghost !px-3" onClick={() => shiftDay(-1)} aria-label="Previous day">‹</button>
            <input id="pc-date" type="date" className="field !w-auto min-w-0 flex-1" value={date} onChange={(e) => e.target.value && setDate(e.target.value)} />
            <button className="btn btn-ghost !px-3" onClick={() => shiftDay(1)} aria-label="Next day">›</button>
            <button className="btn btn-ghost" onClick={() => setDate(todayIn(place.timezone))}>Today</button>
          </div>
        </div>
      </section>

      <div aria-live="polite" aria-busy={busy} className={busy && shown ? "opacity-60 transition-opacity" : ""}>
        {result?.error && !busy && <div role="alert" className="card p-4 text-sm text-danger">{result.error}</div>}
        {!shown && !result?.error && <div className="card h-64 animate-pulse" aria-label="Loading panchang" />}
        {shown && <PanchangView p={shown} place={place} />}
      </div>
    </div>
  );
}

export default dynamic(() => Promise.resolve(PanchangApp), {
  ssr: false,
  loading: () => <div className="card mt-2 h-64 animate-pulse" aria-label="Loading panchang" />,
});

function PanchangView({ p, place }: { p: PanchangResponse; place: Place | null }) {
  const tithi = p.tithi[0];
  return (
    <div className={`space-y-6`}>
      <header>
        <p className="text-sm text-ink-3">
          {new Date(`${p.date}T12:00:00Z`).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })}
          {place && ` · ${place.name}`}
        </p>
        <h1 className="mt-1 font-display text-3xl font-semibold sm:text-4xl">
          {p.masa.adhika && "Adhika "}{p.masa.name} · {tithi.index === 15 || tithi.index === 30 ? "" : `${tithi.paksha} `}{tithi.name}
        </h1>
        <p className="mt-1 text-ink-2">{p.vara.name} · at sunrise {fmtLocalTime(p.sunrise)}</p>
      </header>

      <DayStrip p={p} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <LimbCard title="Tithi" spans={p.tithi} day={p.date}
          extra={(s) => (s.index === 15 || s.index === 30 ? undefined : s.paksha)} />
        <LimbCard title="Nakshatra" spans={p.nakshatra} day={p.date} />
        <LimbCard title="Yoga" spans={p.yoga} day={p.date} />
        <LimbCard title="Karana" spans={p.karana} day={p.date} />
      </div>

      <p className="text-xs text-ink-3">
        Hindu day runs sunrise to next sunrise ({fmtLocalTime(p.next_sunrise)} {dayTag(p.next_sunrise, p.date)}).
        Amanta month; sunrise = upper limb with refraction; {p.settings.ayanamsha} ayanamsha; {p.settings.ephemeris}.
      </p>
    </div>
  );
}

function LimbCard({ title, spans, day, extra }: {
  title: string; spans: Span[]; day: string; extra?: (s: Span) => string | undefined;
}) {
  return (
    <section className="card p-4" aria-labelledby={`lc-${title}`}>
      <h2 id={`lc-${title}`} className="text-xs font-semibold uppercase tracking-wider text-ink-3">{title}</h2>
      <ol className="mt-2 space-y-2">
        {spans.map((s, i) => (
          <li key={s.start} className={i === 0 ? "" : "border-t border-line pt-2"}>
            <p className={i === 0 ? "font-display text-2xl font-semibold" : "font-medium"}>
              {extra?.(s) && <span className="text-ink-2">{extra(s)} </span>}{s.name}
            </p>
            <p className="text-sm text-ink-2 tabular-nums">
              {i === 0 ? "until " : `${fmtLocalTime(s.start)} – `}
              {fmtLocalTime(s.end)}
              {dayTag(s.end, day) && <span className="text-ink-3"> {dayTag(s.end, day)}</span>}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}

/** Sunrise → sunset strip with Rahu Kalam, Yamagandam and Gulika marked. */
function DayStrip({ p }: { p: PanchangResponse }) {
  const t = (iso: string) => new Date(iso).getTime();
  const a = t(p.sunrise), b = t(p.sunset);
  const pos = (iso: string) => ((t(iso) - a) / (b - a)) * 100;
  const kalams = [
    { k: "Rahu Kalam", v: p.rahu_kalam, strong: true },
    { k: "Yamagandam", v: p.yamagandam, strong: false },
    { k: "Gulika Kalam", v: p.gulika_kalam, strong: false },
  ];
  return (
    <section className="card p-5" aria-labelledby="ds-h">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="ds-h" className="font-display text-xl font-semibold">Day</h2>
        <p className="text-sm tabular-nums text-ink-2">
          ☀ Sunrise {fmtLocalTime(p.sunrise)} · Sunset {fmtLocalTime(p.sunset)}
        </p>
      </div>
      <div className="relative mt-4 h-10 rounded-lg bg-surface-2" aria-hidden>
        {kalams.map(({ k, v, strong }) => (
          <div key={k} className="absolute top-0 h-full rounded-md"
            style={{ left: `${pos(v.start)}%`, width: `${pos(v.end) - pos(v.start)}%`,
                     background: strong ? "var(--kalam)" : "var(--kalam-soft)" }}
            title={`${k} ${fmtLocalTime(v.start)}–${fmtLocalTime(v.end)}`} />
        ))}
        {[0, 25, 50, 75, 100].map((x) => (
          <div key={x} className="absolute top-full h-1.5 w-px bg-line" style={{ left: `${x}%` }} />
        ))}
      </div>
      <ul className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
        {kalams.map(({ k, v, strong }) => (
          <li key={k} className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm" style={{ background: strong ? "var(--kalam)" : "var(--kalam-soft)" }} aria-hidden />
            <span className="font-medium">{k}</span>
            <span className="tabular-nums text-ink-2">{fmtLocalTime(v.start)} – {fmtLocalTime(v.end)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
