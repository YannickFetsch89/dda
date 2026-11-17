// /konto/willkommen – Alters-Häkchen (nur falls nötig), Interessen-Fragebogen und Abschlussseite (Plan 5.3, 8).
// Die Zahlen je Kategorie kommen aus dem gecachten Pool und sind nicht persönlich.
import type { Metadata } from "next";
import { WillkommenSeite } from "@/components/konto-bereich";
import type { FragebogenDaten } from "@/components/interessen-fragebogen";
import { eventPoolLaden } from "@/lib/daten";
import { filtern, kategorieZaehlen } from "@/lib/ableitungen";
import { plusTage } from "@/lib/datum";
import { KATEGORIEN, katStil } from "@/lib/kategorien";
import { GUIDE_NACHBARSTAEDTE, stadtteilSlug } from "@/lib/landing";
import { BEZIRKE, stadtteilName } from "@/lib/stadtteile";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Willkommen", robots: KONTO_ROBOTS };

async function fragebogenDaten(): Promise<FragebogenDaten> {
  const pool = await eventPoolLaden();
  const zaehler = kategorieZaehlen(filtern(pool.events, { von: pool.heute, bis: plusTage(pool.heute, 29) }));
  return {
    kategorien: KATEGORIEN.map((k) => ({
      slug: k.slug, name: k.name, icon: k.icon, stil: katStil(k.slug), anzahl: zaehler[k.slug] ?? 0,
      unter: k.unterkategorien.map((u) => ({ slug: u.slug, name: u.name })),
    })),
    bezirke: BEZIRKE.map((b) => ({ name: b.name, stadtteile: b.stadtteile.map((s) => ({ slug: stadtteilSlug(s), name: stadtteilName(s) })) })),
    nachbarn: GUIDE_NACHBARSTAEDTE.map((s) => ({ slug: stadtteilSlug(s), name: s })),
  };
}

export default async function Willkommen() {
  return (
    <KontoRahmen titel="Willkommen">
      <WillkommenSeite daten={await fragebogenDaten()} />
    </KontoRahmen>
  );
}
