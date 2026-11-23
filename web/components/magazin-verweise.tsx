// Verweise aufs Magazin an anderen Stellen der Website (Plan docs/plan-redaktion-2026-11-19.md, 5.9, Schritt 7):
// Startseiten-Box „Aus dem Magazin“, „Lesetipp aus dem Magazin“ auf Guide-Hubs, „Die ganze Woche“ auf /wochenende und
// „Erwähnt im Magazin“ auf Event-Seiten. Alle hinter MAGAZIN_VERLINKT; ohne passenden Beitrag rendern sie nichts.
// Daten nur aus den gecachten Ladern (beitraegeLaden, magazinHeute) – kein eigener Datenbankzugriff, kein connection().
import Link from "next/link";
import { BeitragKarte } from "./magazin";
import { Icon } from "./karten";
import { beitragPfad, istVorbei, RUBRIK_NAME, saisonVorbei, type MagazinBeitrag } from "@/lib/magazin";
import { beitraegeLaden, magazinHeute } from "@/lib/magazin-daten";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";

/** Noch aktuell: laufende Ausgabe nicht abgelaufen, Saison nicht vorbei. */
export function aktuell(b: MagazinBeitrag, heute: string): boolean {
  return !istVorbei(b, heute) && !saisonVorbei(b, heute);
}

/** Die neuesten aktuellen Beiträge für die Startseite (beitraegeLaden liefert schon neueste zuerst). */
export function startAuswahl(beitraege: MagazinBeitrag[], heute: string, max = 3): MagazinBeitrag[] {
  return beitraege.filter((b) => aktuell(b, heute)).slice(0, max);
}

/**
 * Lesetipp für einen Guide-Hub: ein aktueller Beitrag, der den Guide einbettet ({{guide:<slug>}}). Bei mehreren gewinnt
 * der mit den meisten eingebetteten Orten (also der, der den Guide wirklich behandelt), dann der neueste.
 */
export function lesetippFuer(beitraege: MagazinBeitrag[], guide: string, heute: string): MagazinBeitrag | null {
  const marke = `{{guide:${guide}}}`;
  const passend = beitraege.filter((b) => aktuell(b, heute) && b.inhalt_md.includes(marke));
  passend.sort((a, b) => b.ort_slugs.length - a.ort_slugs.length || (b.veroeffentlicht_am ?? "").localeCompare(a.veroeffentlicht_am ?? ""));
  return passend[0] ?? null;
}

/** Wochenvorschau, deren Zeitraum die Tage von–bis berührt (z. B. das Wochenende Fr–So); die neueste gewinnt. */
export function wochenvorschauFuer(beitraege: MagazinBeitrag[], von: string, bis: string): MagazinBeitrag | null {
  return (
    beitraege.find(
      (b) => b.rubrik === "wochenvorschau" && !!b.gueltig_von && !!b.gueltig_bis && b.gueltig_von <= bis && b.gueltig_bis >= von,
    ) ?? null
  );
}

/** Beiträge, die ein Event einbetten (event_ids), neueste zuerst, höchstens max. */
export function erwaehntIn(beitraege: MagazinBeitrag[], eventId: string, max = 2): MagazinBeitrag[] {
  return beitraege.filter((b) => b.event_ids.includes(eventId)).slice(0, max);
}

/** Startseite: „Aus dem Magazin“ mit den drei neuesten aktuellen Beiträgen. */
export async function MagazinStartBox() {
  if (!MAGAZIN_VERLINKT) return null;
  const auswahl = startAuswahl(await beitraegeLaden(), await magazinHeute());
  if (!auswahl.length) return null;
  return (
    <section className="sektion" aria-labelledby="mz-start-titel">
      <div className="sektionskopf sektionskopf--stapeln">
        <h2 className="d" id="mz-start-titel">Aus dem Magazin</h2>
        <Link href="/magazin">Alle Beiträge</Link>
      </div>
      <div className="mz-liste" role="list">
        {auswahl.map((b) => <BeitragKarte key={b.id} b={b} />)}
      </div>
    </section>
  );
}

/** Navy-Kasten mit Verweis auf einen Beitrag (gleiche Optik wie der Guide-Kasten im Beitrag). */
function Verweis({ b, zeile }: { b: MagazinBeitrag; zeile: string }) {
  return (
    <Link href={beitragPfad(b)} className="mz-kasten mz-verweis">
      <Icon name="article" />
      <span>
        <strong>{zeile}</strong>
        <span>{b.titel}</span>
      </span>
    </Link>
  );
}

/** Guide-Hub: „Lesetipp aus dem Magazin“, wenn ein Beitrag den Guide einbettet. */
export async function MagazinLesetipp({ guide }: { guide: string }) {
  if (!MAGAZIN_VERLINKT) return null;
  const b = lesetippFuer(await beitraegeLaden(), guide, await magazinHeute());
  return b ? <Verweis b={b} zeile="Lesetipp aus dem Magazin" /> : null;
}

/** /wochenende: „Die ganze Woche“ → die Wochenvorschau, die dieses Wochenende abdeckt. */
export async function WochenvorschauKasten({ von, bis }: { von: string; bis: string }) {
  if (!MAGAZIN_VERLINKT) return null;
  const b = wochenvorschauFuer(await beitraegeLaden(), von, bis);
  return b ? <Verweis b={b} zeile={`Die ganze Woche: ${RUBRIK_NAME.wochenvorschau}`} /> : null;
}

/** Event-Seite: „Erwähnt im Magazin“ (höchstens zwei Beiträge, die das Event einbetten). */
export async function ErwaehntImMagazin({ eventId }: { eventId: string }) {
  if (!MAGAZIN_VERLINKT) return null;
  const liste = erwaehntIn(await beitraegeLaden(), eventId);
  if (!liste.length) return null;
  return (
    <section className="detail__abschnitt" aria-labelledby="mz-erwaehnt">
      <h2 className="d" id="mz-erwaehnt" style={{ fontSize: 22 }}>
        Erwähnt im Magazin
      </h2>
      {liste.map((b) => (
        <Link key={b.id} className="link" href={beitragPfad(b)}>
          {b.titel} <Icon name="arrow_forward" />
        </Link>
      ))}
    </section>
  );
}
