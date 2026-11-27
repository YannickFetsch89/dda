// Umschalter oben auf den Event-Seiten (Auftraggeber 27.11.2026): „Heute“, „Wochenende“ und „Ausblick“ sind aus
// der Tabbar in die Welt „Events“ gewandert. Nur unter 1200 px sichtbar; am Desktop übernimmt das Menü „Events ▾“.
// Server-Komponente: jede Seite sagt selbst, welcher Punkt aktiv ist – so steht die Leiste ohne Layout-Sprung im HTML.
import Link from "next/link";

export type EventsBereich = "alle" | "heute" | "morgen" | "wochenende" | "ausblick" | "kostenlos" | null;

const PUNKTE: { key: Exclude<EventsBereich, null>; href: string; label: string }[] = [
  { key: "alle", href: "/entdecken", label: "Alle" },
  { key: "heute", href: "/heute", label: "Heute" },
  { key: "morgen", href: "/morgen", label: "Morgen" },
  { key: "wochenende", href: "/wochenende", label: "Wochenende" },
  { key: "ausblick", href: "/ausblick", label: "Ausblick" },
  { key: "kostenlos", href: "/kostenlos", label: "Kostenlos" },
];

/** innen: steht schon in einem .container (Entdecken, Kostenlos) – dann ohne eigenen Container */
export function EventsUmschalter({ aktiv, innen = false }: { aktiv: EventsBereich; innen?: boolean }) {
  const leiste = (
    <div className="ev-umschalter__leiste">
      {PUNKTE.map((p) => (
        <Link key={p.key} href={p.href} className={p.key === aktiv ? "chip chip--aktiv" : "chip"} aria-current={p.key === aktiv ? "page" : undefined}>
          {p.label}
        </Link>
      ))}
    </div>
  );
  return (
    <nav className={innen ? "ev-umschalter ev-umschalter--innen nur-mobil" : "ev-umschalter nur-mobil"} aria-label="Events nach Zeitraum">
      {innen ? leiste : <div className="container">{leiste}</div>}
    </nav>
  );
}
