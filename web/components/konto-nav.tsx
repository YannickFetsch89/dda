"use client";
// Gemeinsame Navigation „Mein dies.das“ (Plan Mein Bereich 3.2): Seitenleiste am Desktop auf /konto/* und /merkliste.
// Sichtbar nur bei html[data-konto="1"]. Das regelt CSS schon vor der Hydration; danach setzt die Komponente
// zusätzlich `hidden`, falls CSS fehlt. Der Server schreibt keinen Kontostand ins HTML.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";
import { useHydriert, useKontoZustand } from "./client";

export const KONTO_LINKS = [
  { href: "/konto", label: "Übersicht", icon: "person" },
  { href: "/konto/fuer-dich", label: "Für dich", icon: "auto_awesome" },
  { href: "/merkliste", label: "Merkliste", icon: "favorite" },
  { href: "/konto/erlebt", label: "Erlebt", icon: "history" },
  { href: "/konto/interessen", label: "Interessen", icon: "interests" },
  { href: "/konto/einstellungen", label: "Konto und Sicherheit", icon: "shield_person" },
  { href: "/konto/datenschutz", label: "Datenschutz", icon: "privacy_tip" },
] as const;

/** Seitenleiste; eigene Suspense-Grenze, weil usePathname sonst das Vorrendern blockiert */
export function KontoSeitenleiste() {
  // `hidden` erst nach der Hydration: Im Server-HTML (immer „abgemeldet“) würde es die Leiste vor der Hydration
  // verdecken, obwohl CSS sie bei html[data-konto="1"] schon zeigt (Cursor-Befund 2)
  const zustand = useKontoZustand();
  const hydriert = useHydriert();
  const an = !hydriert || zustand === "1";
  return (
    <Suspense fallback={<Leiste pfad={null} an={an} />}>
      <LeisteMitPfad an={an} />
    </Suspense>
  );
}

function LeisteMitPfad({ an }: { an: boolean }) {
  return <Leiste pfad={usePathname()} an={an} />;
}

function Leiste({ pfad, an }: { pfad: string | null; an: boolean }) {
  return (
    <nav className="konto-nav" aria-label="Mein dies.das" hidden={!an}>
      <ul>
        {KONTO_LINKS.map((l) => (
          <li key={l.href}>
            <Link href={l.href} aria-current={pfad === l.href ? "page" : undefined}>
              <span className="icon" aria-hidden data-icon={l.icon} />
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
