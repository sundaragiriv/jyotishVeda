"use client";

import { useEffect, useId, useRef, useState } from "react";
import { ApiError, Place, searchPlaces } from "@/lib/api";

/**
 * Accessible place combobox (WAI-ARIA combobox pattern):
 * type to search, ↑/↓ to move, Enter to choose, Esc to close.
 */
export default function PlaceSearch({
  value, onChange, label = "Place of birth",
}: { value: Place | null; onChange: (p: Place | null) => void; label?: string }) {
  const id = useId();
  const [query, setQuery] = useState(value ? fmt(value) : "");
  const [results, setResults] = useState<Place[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "empty">("idle");
  const [error, setError] = useState("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inflight = useRef<AbortController | null>(null);

  // A place chosen from outside (e.g. "Try an example") replaces the text
  // without searching (React's "adjust state when a prop changes" pattern).
  const [shownValue, setShownValue] = useState(value);
  if (value !== shownValue) {
    setShownValue(value);
    if (value) { setQuery(fmt(value)); setOpen(false); }
  }

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); inflight.current?.abort(); }, []);

  // Search runs from the input's change handler, debounced
  const onType = (text: string) => {
    setQuery(text);
    if (value) onChange(null);
    if (timer.current) clearTimeout(timer.current);
    inflight.current?.abort();
    const q = text.trim();
    if (q.length < 2) { setResults([]); setStatus("idle"); setOpen(false); return; }
    timer.current = setTimeout(async () => {
      const ctrl = new AbortController();
      inflight.current = ctrl;
      setStatus("loading");
      setOpen(true);
      try {
        const r = await searchPlaces(q, ctrl.signal);
        setResults(r.results);
        setStatus(r.results.length ? "idle" : "empty");
        setActive(r.results.length ? 0 : -1);
      } catch (e) {
        if (ctrl.signal.aborted) return;
        setStatus("error");
        setError(e instanceof ApiError ? e.message : "Place search failed.");
      }
    }, 220);
  };

  const choose = (p: Place) => {
    onChange(p);
    setShownValue(p);
    setQuery(fmt(p));
    setOpen(false);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setOpen(true); setActive((a) => Math.min(a + 1, results.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    else if (e.key === "Enter" && open && active >= 0 && results[active]) { e.preventDefault(); choose(results[active]); }
    else if (e.key === "Escape") setOpen(false);
  };

  const listId = `${id}-list`;
  return (
    <div className="relative">
      <label htmlFor={id} className="label">{label}</label>
      <input
        id={id}
        className="field"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open && active >= 0 ? `${id}-opt-${active}` : undefined}
        autoComplete="off"
        placeholder="e.g. Machilipatnam"
        value={query}
        onChange={(e) => onType(e.target.value)}
        onKeyDown={onKey}
        onFocus={() => results.length && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {value && (
        <p className="mt-1 text-xs text-ink-3">
          {value.latitude.toFixed(3)}°, {value.longitude.toFixed(3)}° · {value.timezone}
        </p>
      )}
      {open && (
        <ul id={listId} role="listbox" aria-label="Matching places"
          className="card absolute z-20 mt-1 max-h-72 w-full overflow-auto p-1 shadow-lg">
          {status === "loading" && <li className="px-3 py-2 text-sm text-ink-3">Searching…</li>}
          {status === "empty" && <li className="px-3 py-2 text-sm text-ink-3">No places match “{query}”. Try the nearest town.</li>}
          {status === "error" && <li className="px-3 py-2 text-sm text-danger">{error}</li>}
          {status === "idle" && results.map((p, i) => (
            <li
              key={p.id}
              id={`${id}-opt-${i}`}
              role="option"
              aria-selected={i === active}
              onMouseDown={(e) => { e.preventDefault(); choose(p); }}
              onMouseEnter={() => setActive(i)}
              className={`cursor-pointer rounded-lg px-3 py-2 ${i === active ? "bg-surface-2" : ""}`}
            >
              <span className="font-medium">{p.name}</span>
              <span className="text-sm text-ink-3"> · {p.region.includes(",") ? p.region : p.country}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function fmt(p: Place) {
  return `${p.name}, ${p.region.includes(",") ? p.region : p.country}`;
}
