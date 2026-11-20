// „Nächste Events“ auf Guide-Seiten (Clubs, Kneipen, Restaurants & Cafés) – Plan docs/plan-locations-2026-11-18.md,
// 3.2, 3.6, 3.9: dieselbe Abfrage über events.ort_id wie die Ortsseiten (Haus plus Säle), nicht der 60-Tage-Pool.
// „nicht im …“-Events haben keine ort_id und erscheinen deshalb nicht. Säle mit eigener Seite werden verlinkt.
import Link from "next/link";
import { Reihe } from "./client";
import { EventKarte } from "./karten";
import { ortSeitePfad } from "@/lib/spielstaetten";
import { kinderVon, programmLaden, spielstaettenLaden } from "@/lib/spielstaetten-daten";
import type { DddOrt } from "@/lib/typen";

export async function OrtProgramm({ ort, titel = "Nächste Events hier" }: { ort: DddOrt; titel?: string }) {
  const { orte } = await spielstaettenLaden();
  const saele = kinderVon(ort.id, orte);
  const programm = await programmLaden([ort.id, ...saele.map((s) => s.id)].sort());
  if (programm.fehler || !programm.events.length) return null;
  const events = programm.events.slice(0, 10);
  return (
    <section className="gd-abschnitt">
      <div className="gd-abschnitt__kopf">
        <h2 className="d">{titel}</h2>
        <span className="muted">{programm.events.length} Termine</span>
      </div>
      {saele.length > 0 && (
        <nav className="os-saele" aria-label="Säle">
          {saele.map((s) => (
            <Link key={s.id} href={ortSeitePfad(s.slug)} className="gd-chip">{s.name.replace(`${ort.name} – `, "")}</Link>
          ))}
        </nav>
      )}
      <Reihe breite={258} label={`Events im ${ort.name}`}>
        {events.map((e) => <EventKarte key={e.id} e={e} heute={programm.heute} variante="reihe" />)}
      </Reihe>
    </section>
  );
}
