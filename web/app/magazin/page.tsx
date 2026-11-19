// Magazin-Übersicht (Plan docs/plan-redaktion-2026-11-19.md, 5.1): neuester Beitrag groß, dann chronologisch (30).
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { BeitragKarte, RubrikLinks } from "@/components/magazin";
import { Leer } from "@/components/karten";
import { beitraegeLaden } from "@/lib/magazin-daten";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";
import { seitenMetadaten } from "@/lib/seo";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/magazin",
  titel: "Magazin: Tipps, Wochenvorschau und Stadtleben in Düsseldorf",
  beschreibung: "Was in Düsseldorf los ist: Wochenvorschau, Monats-Tipps, Saison und Stadtleben – ausgewählt und geprüft von der Redaktion.",
  noindex: !MAGAZIN_VERLINKT,
});

export default async function MagazinSeite() {
  const beitraege = (await beitraegeLaden()).slice(0, 30);
  const [erster, ...rest] = beitraege;
  return (
    <div className="container sektion mz-uebersicht">
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <span aria-current="page">Magazin</span>
      </nav>
      <h1 className="d">Magazin</h1>
      <p className="mz-teaser">
        Was in Düsseldorf los ist – ausgewählt aus unseren Daten und geprüft von der <Link href="/magazin/redaktion">Redaktion</Link>.
      </p>
      <RubrikLinks />
      {erster ? (
        <>
          <div className="mz-liste mz-liste--erster" role="list">
            <BeitragKarte b={erster} gross />
          </div>
          {rest.length > 0 && (
            <div className="mz-liste" role="list">
              {rest.map((b) => <BeitragKarte key={b.id} b={b} />)}
            </div>
          )}
        </>
      ) : (
        <Leer titel="Hier erscheinen bald die ersten Beiträge">
          <p>Bis dahin findest du alle Events im Kalender.</p>
          <Link className="btn btn--gold" href="/entdecken">Events entdecken</Link>
        </Leer>
      )}
    </div>
  );
}
