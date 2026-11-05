// „Event melden“ – Veranstalter und Besucher reichen Events ein; Admins geben sie im Dashboard frei.
import type { Metadata } from "next";
import Link from "next/link";
import { EventMeldenForm, type KategorieOption } from "@/components/event-melden-form";
import { KATEGORIEN } from "@/lib/kategorien";

export const metadata: Metadata = {
  title: "Event melden",
  description:
    "Du veranstaltest etwas in Düsseldorf oder hast einen Tipp? Melde dein Event bei dies.das.düsseldorf – kostenlos und in wenigen Minuten.",
  alternates: { canonical: "/event-melden" },
};

// Formularwerte = Datenbank-Werte (Website nennt "family" → "familie")
const KATEGORIE_OPTIONEN: KategorieOption[] = [
  ...KATEGORIEN.map((k) => ({ wert: k.slug === "familie" ? "family" : k.slug, name: k.name })),
  { wert: "sonstiges", name: "Sonstiges" },
];

export default function EventMeldenSeite() {
  return (
    <div className="container sektion event-melden">
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link><span>/</span><span aria-current="page">Event melden</span>
      </nav>
      <h1 className="d">Event melden</h1>
      <p className="event-melden__intro">
        Du veranstaltest etwas in Düsseldorf oder hast einen Tipp, der hier noch fehlt? Erzähl uns davon. Wir prüfen
        jede Meldung und schalten sie anschließend kostenlos frei.
      </p>
      <EventMeldenForm kategorien={KATEGORIE_OPTIONEN} />
    </div>
  );
}
