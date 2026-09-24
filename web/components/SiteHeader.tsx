"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import ThemeToggle from "./ThemeToggle";

const NAV = [
  { href: "/", label: "Chart" },
  { href: "/panchang", label: "Panchang" },
];

export default function SiteHeader() {
  const path = usePathname();
  return (
    <header className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
      <Link href="/" className="flex items-baseline gap-2" aria-label="Jyotisha Veda home">
        <span className="hidden font-deva text-xl text-accent sm:inline" aria-hidden>ज्योतिष</span>
        <span className="whitespace-nowrap font-display text-2xl font-semibold tracking-wide">Jyotisha Veda</span>
      </Link>
      <nav aria-label="Main" className="flex items-center gap-1">
        {NAV.map((n) => {
          const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
          return (
            <Link
              key={n.href}
              href={n.href}
              aria-current={active ? "page" : undefined}
              className={`rounded-lg px-3 py-2 text-sm font-medium ${
                active ? "bg-surface-2 text-ink" : "text-ink-2 hover:text-ink"
              }`}
            >
              {n.label}
            </Link>
          );
        })}
        <ThemeToggle />
      </nav>
    </header>
  );
}
