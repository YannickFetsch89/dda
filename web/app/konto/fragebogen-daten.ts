// Namen und Zahlen für den Interessen-Fragebogen und die Interessen-Übersicht (Plan 5.3, Mein Bereich 3.6).
// Die Zahlen je Kategorie kommen aus dem gecachten Pool und sind nicht persönlich.
import type { FragebogenDaten } from "@/components/interessen-fragebogen";
import { eventPoolLaden } from "@/lib/daten";
import { filtern, kategorieZaehlen } from "@/lib/ableitungen";
import { plusTage } from "@/lib/datum";
import { KATEGORIEN, katStil } from "@/lib/kategorien";
import { GUIDE_NACHBARSTAEDTE, stadtteilSlug } from "@/lib/landing";
import { BEZIRKE, stadtteilName } from "@/lib/stadtteile";

export async function fragebogenDaten(): Promise<FragebogenDaten> {
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
