// Startseiten-Box „Weihnachtsmärkte in Düsseldorf“ mit den heute geöffneten Märkten (Plan Weihnachtsmärkte 5.6): nur bei Schalter an und vom 15.11. bis
// 30.12. Der Tag kommt aus heuteKurz() (höchstens 5 Minuten alt) – nicht aus pool.heute (bis 1 h alt).
// Tagesgenau (ohne Uhrzeit): „heute 11–21 Uhr“. Ohne belegt offenen Markt ein ehrlicher Satz statt „alles zu“.
import Link from "next/link";
import { connection } from "next/server";
import { BildImg, Reihe } from "./client";
import { Icon } from "./karten";
import { WM_BILD, wmIcon } from "./wm-karte";
import { WEIHNACHTSMAERKTE_VERLINKT } from "@/lib/schalter";
import { ortBildFokus, ortBildUrl } from "@/lib/orte";
import { stadtteilName } from "@/lib/stadtteile";
import { WM_BASIS, oeffnungAm, sortieren, wm, wmPfad, zeitText } from "@/lib/weihnachtsmaerkte";
import { heuteKurz, weihnachtsmaerkteLaden } from "@/lib/weihnachtsmaerkte-daten";

/** Datumsfenster der Box (rein, getestet). */
export function startboxAktiv(heute: string, verlinkt = WEIHNACHTSMAERKTE_VERLINKT): boolean {
  const md = heute.slice(5);
  return verlinkt && md >= "11-15" && md <= "12-30";
}

/** Höchstens so viele Karten in der Reihe; der Rest über „+N weitere“ und die gefilterte Übersicht (19.11.2026). */
export const STARTBOX_MAX = 10;

export async function WmStartBox() {
  await connection(); // Tag zur Anfrage, nie beim Vorrendern
  const heute = await heuteKurz();
  if (!startboxAktiv(heute)) return null;
  const alle = sortieren(await weihnachtsmaerkteLaden());
  if (!alle.length) return null;
  // Reihenfolge wie im Guide (Empfehlung zuerst); Gruppen haben keine eigenen Zeiten
  const offen = alle
    .filter((o) => !wm(o).ist_gruppe)
    .map((o) => ({ o, x: oeffnungAm(wm(o).saisons, heute) }))
    .filter(({ x }) => x.zustand === "offen");
  const gezeigt = offen.slice(0, STARTBOX_MAX);
  const rest = offen.length - gezeigt.length;
  const offenHref = `${WM_BASIS}?offen=1`;
  return (
    <section className="sektion wm-startbox" aria-labelledby="wm-startbox-titel">
      <div className="sektionskopf sektionskopf--stapeln">
        {/* Titel und Link (Auftraggeber 25.11.2026): immer „Alle Weihnachtsmärkte“ auf die ungefilterte Übersicht;
            nur die „+N weitere“-Karte führt zur Liste der heute geöffneten Märkte */}
        <h2 className="d" id="wm-startbox-titel"><Icon name="wm:markt" /> Weihnachtsmärkte in Düsseldorf</h2>
        <Link href={WM_BASIS}>Alle Weihnachtsmärkte</Link>
      </div>
      {offen.length ? (
        // Bildkarten in einer waagerechten Reihe: bleibt bei 4 wie bei 20 offenen Märkten übersichtlich (Auftraggeber 19.11.2026)
        <Reihe breite={240} label="Weihnachtsmärkte heute geöffnet">
          {gezeigt.map(({ o, x }) => (
            <article key={o.id} className="wm-startkarte" role="listitem">
              <Link href={wmPfad(o)} className="wm-startkarte__link">
                <span className="wm-startkarte__bild">
                  <BildImg src={ortBildUrl(o) ?? WM_BILD} ersatz={ortBildUrl(o) ? WM_BILD : null} alt="" icon={wmIcon(o)} fokus={ortBildFokus(o)} />
                </span>
                <span className="wm-startkarte__text">
                  <span className="wm-startkarte__name">{o.name}</span>
                  <span className="wm-startkarte__meta">
                    {[o.stadtteil ? stadtteilName(o.stadtteil) : null, `heute ${zeitText(x.von, x.bis)}`].filter(Boolean).join(" · ")}
                  </span>
                </span>
              </Link>
            </article>
          ))}
          {rest > 0 && (
            <article className="wm-startkarte wm-startkarte--mehr" role="listitem">
              <Link href={offenHref} className="wm-startkarte__link">
                <span className="wm-startkarte__mehr-zahl">+{rest}</span>
                <span>weitere Märkte heute geöffnet</span>
              </Link>
            </article>
          )}
        </Reihe>
      ) : (
        <p className="muted">
          Heute ist kein Markt als geöffnet belegt. In der <Link href={WM_BASIS}>Übersicht</Link> seht ihr, wo die Zeiten fehlen und wann es weitergeht.
        </p>
      )}
    </section>
  );
}
