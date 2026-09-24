/** Typed client for the Jyotisha Veda API (see api/main.py). */

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Place {
  id: number;
  name: string;
  region: string;
  country: string;
  latitude: number;
  longitude: number;
  timezone: string;
  population: number;
}

export interface Graha {
  graha: string;
  longitude: number;
  longitude_dms: string;
  speed_deg_per_day: number;
  retrograde: boolean;
  rasi_index: number;
  rasi: string;
  rasi_lord: string;
  degree_in_rasi: number;
  degree_in_rasi_dms: string;
  nakshatra_index: number;
  nakshatra: string;
  nakshatra_lord: string;
  pada: number;
  house: number;
  bhava?: number;
}

export interface Point {
  longitude: number;
  longitude_dms: string;
  rasi_index: number;
  rasi: string;
  degree_in_rasi_dms: string;
  nakshatra: string;
  pada: number;
}

export interface VargaCell {
  rasi_index: number;
  rasi: string;
  longitude: number;
}

export interface DashaPeriod {
  lord: string;
  level: string;
  start: string;
  end: string;
  years: number;
  periods?: DashaPeriod[];
}

export interface ChartResponse {
  input: { utc: string; latitude: number; longitude: number };
  settings: { ayanamsha: string; ayanamsha_dms: string; node: string; ephemeris: string; house_system: string };
  lagna: Point;
  grahas: Graha[];
  vargas: Record<string, Record<string, VargaCell>>;
  dasha: {
    moon_nakshatra: string;
    starting_lord: string;
    balance_at_birth: { lord: string; years: number };
    periods: DashaPeriod[];
    current: { lord: string; level: string; start: string; end: string }[];
  };
}

export interface Span {
  index: number;
  name: string;
  start: string;
  end: string;
  paksha?: string;
}

export interface PanchangResponse {
  date: string;
  location: { tz: string };
  settings: { sunrise: string; ayanamsha: string; ephemeris: string };
  sunrise: string;
  sunset: string;
  next_sunrise: string;
  vara: { index: number; name: string };
  tithi: Span[];
  nakshatra: Span[];
  yoga: Span[];
  karana: Span[];
  rahu_kalam: { start: string; end: string };
  yamagandam: { start: string; end: string };
  gulika_kalam: { start: string; end: string };
  masa: { name: string; adhika: boolean; starts: string; ends: string };
}

export interface ChartOptions {
  ayanamsha: "lahiri" | "true_chitra" | "raman" | "krishnamurti";
  node: "mean" | "true";
  house_system: string;
}

export class ApiError extends Error {}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(
      `Can't reach the calculation service at ${API_URL}. Check that the API is running.`,
    );
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail);
  }
  return res.json() as Promise<T>;
}

export function searchPlaces(q: string, signal?: AbortSignal) {
  return call<{ results: Place[] }>(`/v1/places?q=${encodeURIComponent(q)}`, { signal });
}

export function fetchChart(birth: {
  local_datetime: string;
  tz?: string;
  utc_offset_minutes?: number;
  latitude: number;
  longitude: number;
}, options: ChartOptions) {
  return call<ChartResponse>("/v1/chart", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      birth,
      options: { ...options, dasha_depth: 2, vargas: [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60] },
    }),
  });
}

export function fetchPanchang(p: { date: string; latitude: number; longitude: number; tz: string }) {
  const q = new URLSearchParams({
    date: p.date,
    latitude: String(p.latitude),
    longitude: String(p.longitude),
    tz: p.tz,
  });
  return call<PanchangResponse>(`/v1/panchang?${q}`);
}
