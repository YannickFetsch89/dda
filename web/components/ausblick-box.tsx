// Startseiten-Box „Große Events später im Jahr“ (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1 Q10, Schritt W2):
// sechs Einträge aus dem Ausblick (Rang 1–2, Orte mit Ortsseite, nach Datum) und Link auf /ausblick.
// Eigene Suspense-Grenze auf der Startseite: der Fernpool lädt nach, die Startseite wartet nicht darauf.
import Link from "next/link";
import { Icon, KompaktKarte } from "@/components/karten";
import { Reihe } from "@/components/client";
import { AUSBLICK_BOX, ausblickLaden } from "@/lib/ausblick";

export async function AusblickStartBox() {
  const { heute, events } = await ausblickLaden();
  const auswahl = events.slice(0, AUSBLICK_BOX);
  if (!auswahl.length) return null;
  return (
    <section className="sektion" aria-labelledby="ausblick-start-titel">
      <div className="sektionskopf sektionskopf--stapeln">
        <h2 className="d" id="ausblick-start-titel">Große Events später im Jahr</h2>
        <Link href="/ausblick">
          Zum Ausblick <Icon name="arrow_forward" />
        </Link>
      </div>
      <div className="nur-mobil">
        <Reihe breite={280} label="Große Events später im Jahr">
          {auswahl.map((e) => <KompaktKarte key={e.id} e={e} heute={heute} />)}
        </Reihe>
      </div>
      <div className="picks-raster nur-desktop" role="list">
        {auswahl.map((e) => <KompaktKarte key={e.id} e={e} heute={heute} />)}
      </div>
    </section>
  );
}
