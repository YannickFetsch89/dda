// Startseiten-Box „Weihnachtsmärkte heute geöffnet“ (Plan Weihnachtsmärkte 5.6): nur bei Schalter an und vom 15.11. bis
// 30.12. Der Tag kommt aus heuteKurz() (höchstens 5 Minuten alt) – nicht aus pool.heute (bis 1 h alt).
// Tagesgenau (ohne Uhrzeit): „heute 11–21 Uhr“. Ohne belegt offenen Markt ein ehrlicher Satz statt „alles zu“.
import Link from "next/link";
import { connection } from "next/server";
import { Icon } from "./karten";
import { WEIHNACHTSMAERKTE_VERLINKT } from "@/lib/schalter";
import { stadtteilName } from "@/lib/stadtteile";
import { WM_BASIS, oeffnungAm, sortieren, wm, wmPfad, zeitText } from "@/lib/weihnachtsmaerkte";
import { heuteKurz, weihnachtsmaerkteLaden } from "@/lib/weihnachtsmaerkte-daten";

/** Datumsfenster der Box (rein, getestet). */
export function startboxAktiv(heute: string, verlinkt = WEIHNACHTSMAERKTE_VERLINKT): boolean {
  const md = heute.slice(5);
  return verlinkt && md >= "11-15" && md <= "12-30";
}

export async function WmStartBox() {
  await connection(); // Tag zur Anfrage, nie beim Vorrendern
  const heute = await heuteKurz();
  if (!startboxAktiv(heute)) return null;
  const alle = sortieren(await weihnachtsmaerkteLaden());
  if (!alle.length) return null;
  const offen = alle
    .filter((o) => !wm(o).ist_gruppe)
    .map((o) => ({ o, x: oeffnungAm(wm(o).saisons, heute) }))
    .filter(({ x }) => x.zustand === "offen")
    .slice(0, 4);
  return (
    <section className="sektion wm-startbox" aria-labelledby="wm-startbox-titel">
      <div className="sektionskopf">
        <h2 className="d" id="wm-startbox-titel"><Icon name="wm:markt" /> Weihnachtsmärkte heute geöffnet</h2>
        <Link href={WM_BASIS}>Alle Weihnachtsmärkte</Link>
      </div>
      {offen.length ? (
        <ul className="wm-startbox__liste">
          {offen.map(({ o, x }) => (
            <li key={o.id}>
              <Link href={wmPfad(o)}>{o.name}</Link>
              <span className="muted">
                {[o.stadtteil ? stadtteilName(o.stadtteil) : null, `heute ${zeitText(x.von, x.bis)}`].filter(Boolean).join(" · ")}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">
          Heute ist kein Markt als geöffnet belegt. In der <Link href={WM_BASIS}>Übersicht</Link> seht ihr, wo die Zeiten fehlen und wann es weitergeht.
        </p>
      )}
    </section>
  );
}
