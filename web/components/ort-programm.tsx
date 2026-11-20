// „Nächste Events“ auf Guide-Seiten (Clubs, Kneipen, Restaurants & Cafés) – Plan docs/plan-locations-2026-11-18.md,
// 3.2, 3.6, 3.9: dieselbe Abfrage über events.ort_id wie die Ortsseiten (Haus plus Säle), nicht der 60-Tage-Pool.
// „nicht im …“-Events haben keine ort_id und erscheinen deshalb nicht. Bei Sälen derselbe Saal-Filter wie auf der
// Ortsseite: „Alle“, je Saal (mit Link auf seine Seite) und „Haus allgemein“ für Events ohne erkennbaren Saal.
import { Reihe } from "./client";
import { EventKarte } from "./karten";
import { SaalFilter, type SaalGruppe } from "./saal-filter";
import { ortSeitePfad } from "@/lib/spielstaetten";
import { kinderVon, programmLaden, spielstaettenLaden } from "@/lib/spielstaetten-daten";
import type { DddEvent, DddOrt } from "@/lib/typen";

const MAX = 10;

export async function OrtProgramm({ ort, titel = "Nächste Events hier" }: { ort: DddOrt; titel?: string }) {
  const { orte } = await spielstaettenLaden();
  const saele = kinderVon(ort.id, orte);
  const programm = await programmLaden([ort.id, ...saele.map((s) => s.id)].sort());
  if (programm.fehler || !programm.events.length) return null;
  const reihe = (events: DddEvent[], label: string) => (
    <Reihe breite={258} label={label}>
      {events.slice(0, MAX).map((e) => <EventKarte key={e.id} e={e} heute={programm.heute} variante="reihe" />)}
    </Reihe>
  );
  const kopf = (
    <div className="gd-abschnitt__kopf">
      <h2 className="d">{titel}</h2>
      <span className="muted">{programm.events.length} Termine</span>
    </div>
  );
  if (!saele.length) {
    return <section className="gd-abschnitt">{kopf}{reihe(programm.events, `Events im ${ort.name}`)}</section>;
  }
  const kurz = (name: string) => name.replace(`${ort.name} – `, "");
  const gruppe = (id: string, label: string, href: string | null, events: DddEvent[]): SaalGruppe =>
    ({ id, label, href, anzahl: events.length, inhalt: reihe(events, `Events: ${label}`) });
  const haus = programm.events.filter((e) => e.ort_id === ort.id);
  const gruppen: SaalGruppe[] = [
    gruppe("alle", "Alle", null, programm.events),
    ...saele.map((s) => gruppe(s.id, kurz(s.name), ortSeitePfad(s.slug), programm.events.filter((e) => e.ort_id === s.id))),
    ...(haus.length ? [gruppe("haus", "Haus allgemein", null, haus)] : []),
  ];
  return <section className="gd-abschnitt">{kopf}<SaalFilter gruppen={gruppen} /></section>;
}
