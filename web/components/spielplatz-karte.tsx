// Schmale Spielplatz-Karte (Plan 5.3/5.4): Name, Typ, Alter, Größe – für „In der Nähe“ und die Guide-Stadtteilseiten.
// Keine Bewertung, keine Score-Zahl.
import Link from "next/link";
import { BildImg } from "./client";
import { Icon } from "./karten";
import { ortBildUrl } from "@/lib/orte";
import { GERAETE, alterInfo, belegteGeraete, entfernungText, groesseText, spielplatz, typInfo } from "@/lib/spielplaetze";
import { spielplatzPfad } from "@/lib/spielplaetze-json-ld";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddOrt } from "@/lib/typen";

/** Alters-Badge in der Altersfarbe (Text immer dabei, die Farbe trägt keine Information allein). */
export function AlterBadge({ o, gross = false }: { o: DddOrt; gross?: boolean }) {
  const a = alterInfo(o);
  if (!a) return null;
  return (
    <span className={`sp-alter sp-alter--${a.wert} ${gross ? "sp-alter--gross" : ""}`}>
      {gross && <span className="sp-alter__kreis" aria-hidden><Icon name="child_care" /></span>}
      {a.vermutlich && <span className="sp-alter__vermutlich">vermutlich</span>}
      {a.wert === "alle" ? "alle Altersgruppen" : a.label}
    </span>
  );
}

export function SpielplatzKarte({ o, meter }: { o: DddOrt; meter?: number | null }) {
  const sp = spielplatz(o);
  const typ = typInfo(o);
  const geraete = belegteGeraete(sp).slice(0, 4).map((g) => GERAETE.find((x) => x.wert === g)!);
  const groesse = groesseText(sp)?.replace(" laut Stadt", "");
  return (
    <article className="gd-karte sp-karte" role="listitem">
      <Link href={spielplatzPfad(o)} className="gd-karte__link">
        <div className="gd-karte__bild">
          <BildImg src={ortBildUrl(o)} ersatz={typ.bild} alt="" icon={typ.icon} />
        </div>
        <div className="gd-karte__text">
          <span className="gd-typ"><Icon name={typ.icon} />{typ.label}</span>
          <h3 className="gd-karte__name d">{o.name}</h3>
          <span className="gd-karte__meta">
            {o.stadtteil && <span className="gd-karte__ort"><Icon name="location_on" />{stadtteilName(o.stadtteil)}</span>}
            {meter != null && <span className="muted">{entfernungText(meter)}</span>}
            {groesse && <span className="muted">{groesse}</span>}
          </span>
          <AlterBadge o={o} />
          {geraete.length > 0 && (
            <span className="sp-geraete" aria-label={`Ausstattung: ${geraete.map((g) => g.label).join(", ")}`}>
              {geraete.map((g) => <span key={g.wert} className="sp-geraet" title={g.label}><Icon name={g.icon} /></span>)}
            </span>
          )}
        </div>
      </Link>
    </article>
  );
}
