"use client";

import { useState } from "react";
import { ChartOptions, Place } from "@/lib/api";
import PlaceSearch from "./PlaceSearch";

export interface BirthData {
  name: string;
  date: string;   // yyyy-mm-dd
  time: string;   // hh:mm or hh:mm:ss
  place: Place;
  options: ChartOptions;
}

const EXAMPLE: BirthData = {
  name: "Swami Vivekananda",
  date: "1863-01-12",
  time: "06:33",
  place: {
    id: 1275004, name: "Kolkata", region: "IN", country: "India",
    latitude: 22.56263, longitude: 88.36304, timezone: "Asia/Kolkata", population: 4631392,
  },
  options: { ayanamsha: "lahiri", node: "mean", house_system: "W" },
};

export default function BirthForm({
  onSubmit, busy,
}: { onSubmit: (b: BirthData) => void; busy: boolean }) {
  const [name, setName] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [place, setPlace] = useState<Place | null>(null);
  const [options, setOptions] = useState<ChartOptions>(EXAMPLE.options);
  const [touched, setTouched] = useState(false);

  const missing = [!date && "date", !time && "time", !place && "place"].filter(Boolean) as string[];

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (missing.length || !place) return;
    onSubmit({ name: name.trim(), date, time, place, options });
  };

  const loadExample = () => {
    setName(EXAMPLE.name); setDate(EXAMPLE.date); setTime(EXAMPLE.time);
    setPlace(EXAMPLE.place); setOptions(EXAMPLE.options);
    onSubmit(EXAMPLE);
  };

  return (
    <form onSubmit={submit} className="card space-y-4 p-5" noValidate aria-label="Birth details">
      <div>
        <h2 className="font-display text-2xl font-semibold">Birth details</h2>
        <p className="text-sm text-ink-2">Local time at the place of birth.</p>
      </div>

      <div>
        <label htmlFor="bf-name" className="label">Name <span className="text-ink-3">(optional)</span></label>
        <input id="bf-name" className="field" value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="bf-date" className="label">Date</label>
          <input id="bf-date" type="date" className="field" value={date} min="1600-01-01" max="2400-12-31"
            onChange={(e) => setDate(e.target.value)} aria-invalid={touched && !date} />
        </div>
        <div>
          <label htmlFor="bf-time" className="label">Time</label>
          <input id="bf-time" type="time" step={1} className="field" value={time}
            onChange={(e) => setTime(e.target.value)} aria-invalid={touched && !time} />
        </div>
      </div>

      <PlaceSearch value={place} onChange={setPlace} />

      <details className="rounded-lg border border-line px-3 py-2 text-sm">
        <summary className="cursor-pointer py-1 font-medium text-ink-2">Calculation settings</summary>
        <div className="mt-3 grid gap-3">
          <div>
            <label htmlFor="bf-ayan" className="label">Ayanamsha</label>
            <select id="bf-ayan" className="field" value={options.ayanamsha}
              onChange={(e) => setOptions({ ...options, ayanamsha: e.target.value as ChartOptions["ayanamsha"] })}>
              <option value="lahiri">Lahiri (Chitrapaksha)</option>
              <option value="true_chitra">True Chitra</option>
              <option value="raman">B.V. Raman</option>
              <option value="krishnamurti">Krishnamurti (KP)</option>
            </select>
          </div>
          <div>
            <label htmlFor="bf-node" className="label">Rahu / Ketu</label>
            <select id="bf-node" className="field" value={options.node}
              onChange={(e) => setOptions({ ...options, node: e.target.value as ChartOptions["node"] })}>
              <option value="mean">Mean node</option>
              <option value="true">True node</option>
            </select>
          </div>
        </div>
      </details>

      {touched && missing.length > 0 && (
        <p role="alert" className="text-sm text-danger">
          Add the {missing.join(", ").replace(/, ([^,]*)$/, " and $1")} to cast the chart.
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <button type="submit" className="btn btn-primary flex-1" disabled={busy}>
          {busy ? "Calculating…" : "Cast chart"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={loadExample} disabled={busy}>
          Try an example
        </button>
      </div>
    </form>
  );
}
