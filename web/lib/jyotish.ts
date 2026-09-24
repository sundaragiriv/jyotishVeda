/** Display names and helpers for classical Jyotish terms. */

export const RASIS = [
  "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
  "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
];

export const RASI_SHORT = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"];

export type LabelScript = "en" | "sa";

export const GRAHA_LABEL: Record<string, { en: string; sa: string; full: string }> = {
  Lagna:   { en: "As", sa: "ल",  full: "Lagna" },
  Surya:   { en: "Su", sa: "सू", full: "Surya · Sun" },
  Chandra: { en: "Mo", sa: "चं", full: "Chandra · Moon" },
  Mangala: { en: "Ma", sa: "मं", full: "Mangala · Mars" },
  Budha:   { en: "Me", sa: "बु", full: "Budha · Mercury" },
  Guru:    { en: "Ju", sa: "गु", full: "Guru · Jupiter" },
  Shukra:  { en: "Ve", sa: "शु", full: "Shukra · Venus" },
  Shani:   { en: "Sa", sa: "श",  full: "Shani · Saturn" },
  Rahu:    { en: "Ra", sa: "रा", full: "Rahu" },
  Ketu:    { en: "Ke", sa: "के", full: "Ketu" },
};

export const VARGAS: { n: number; name: string; area: string }[] = [
  { n: 1, name: "Rasi", area: "Body, overall life" },
  { n: 2, name: "Hora", area: "Wealth" },
  { n: 3, name: "Drekkana", area: "Siblings, courage" },
  { n: 4, name: "Chaturthamsa", area: "Property, fortune" },
  { n: 7, name: "Saptamsa", area: "Children" },
  { n: 9, name: "Navamsa", area: "Spouse, dharma" },
  { n: 10, name: "Dasamsa", area: "Career" },
  { n: 12, name: "Dwadasamsa", area: "Parents" },
  { n: 16, name: "Shodasamsa", area: "Vehicles, comforts" },
  { n: 20, name: "Vimsamsa", area: "Spiritual practice" },
  { n: 24, name: "Chaturvimsamsa", area: "Learning" },
  { n: 27, name: "Bhamsa", area: "Strength, weakness" },
  { n: 30, name: "Trimsamsa", area: "Misfortune" },
  { n: 40, name: "Khavedamsa", area: "Maternal legacy" },
  { n: 45, name: "Akshavedamsa", area: "Paternal legacy, character" },
  { n: 60, name: "Shashtyamsa", area: "Past karma, all matters" },
];

export const GRAHA_ORDER = ["Surya", "Chandra", "Mangala", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu"];

export interface Placement {
  body: string;       // "Surya" ... "Lagna"
  rasi: number;       // 1-12
  degree?: number;    // degrees within rasi, for sorting / tooltips
  retrograde?: boolean;
}

/** Placements of all bodies in a varga, from the API chart response. */
export function vargaPlacements(
  chart: { vargas: Record<string, Record<string, { rasi_index: number; longitude: number }>>;
           grahas: { graha: string; retrograde: boolean }[] },
  n: number,
): { lagnaRasi: number; placements: Placement[] } {
  const key = `D${n}`;
  const retro = Object.fromEntries(chart.grahas.map((g) => [g.graha, g.retrograde]));
  const placements: Placement[] = [];
  let lagnaRasi = 1;
  for (const [body, cells] of Object.entries(chart.vargas)) {
    const c = cells[key];
    if (!c) continue;
    if (body === "Lagna") lagnaRasi = c.rasi_index;
    placements.push({
      body,
      rasi: c.rasi_index,
      degree: c.longitude % 30,
      // Rahu/Ketu (mean node) are always retrograde; marking them adds noise
      retrograde: body !== "Rahu" && body !== "Ketu" ? retro[body] : false,
    });
  }
  return { lagnaRasi, placements };
}

export function fmtDate(iso: string, opts: Intl.DateTimeFormatOptions = { dateStyle: "medium" }) {
  return new Date(iso).toLocaleDateString("en-IN", opts);
}

/** Time of an ISO timestamp shown in the timestamp's own offset (the place's local time). */
export function fmtLocalTime(iso: string) {
  const m = iso.match(/T(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : iso;
}

/** "Wed 10 Apr" when a time falls on a different civil date than `day`. */
export function dayTag(iso: string, day: string) {
  const d = iso.slice(0, 10);
  if (d === day) return "";
  const dt = new Date(`${d}T12:00:00Z`);
  return dt.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
}
