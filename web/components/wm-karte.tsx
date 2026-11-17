// Karten des Weihnachtsmarkt-Guides (Plan 5.2): Bild, Rolle, Name, Stadtteil, Zeitraum, Zustand heute, bis zu drei Badges.
// Der Zustand kommt entweder fertig vom Server (gewählter Tag, ?tag=) oder aus der Browser-Insel (heute, Plan E5).
import Link from "next/link";
import { BildImg } from "./client";
import { Icon } from "./karten";
import { WmZustand } from "./wm-zustand";
import { ortBildFokus, ortBildUrl } from "@/lib/orte";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddOrt } from "@/lib/typen";
import {
  aktuelleSaison, badges, datumKurz, oeffnungAm, oeffnungText, rolleText, saisonsKompakt, wm, wmPfad, type Badge,
} from "@/lib/weihnachtsmaerkte";

export const WM_BILD = "/guides/weihnachtsmaerkte.webp";

export function wmIcon(o: DddOrt): string {
  const d = wm(o);
  if (d.attraktion) return d.art.includes("eisbahn") ? "ice_skating" : "attractions";
  return "wm:markt";
}

export function BadgeListe({ liste, max = 3 }: { liste: Badge[]; max?: number }) {
  if (!liste.length) return null;
  return (
    <span className="wm-badges">
      {liste.slice(0, max).map((b) => (
        <span key={b.wert} className={`wm-badge wm-badge--${b.wert}`}><Icon name={b.icon} />{b.label}</span>
      ))}
    </span>
  );
}

/** Zustandszeile: mit gewähltem Tag fertig vom Server, sonst Browser-Insel. */
export function WmZustandZeile({ o, tag }: { o: DddOrt; tag: string | null }) {
  const saisons = wm(o).saisons;
  if (tag) {
    const x = oeffnungAm(saisons, tag);
    return <span className={`wm-zustand wm-zustand--${x.zustand}`}><span className="wm-zustand__punkt" aria-hidden />{oeffnungText(x, "tag")}</span>;
  }
  return <WmZustand saisons={saisonsKompakt(saisons)} />;
}

export function WmKarte({ o, alle, tag, klein = false }: { o: DddOrt; alle: DddOrt[]; tag: string | null; klein?: boolean }) {
  const bild = ortBildUrl(o);
  const s = aktuelleSaison(wm(o).saisons);
  return (
    <article className={`gd-karte wm-karte${klein ? " wm-karte--klein" : ""}`} role="listitem">
      <Link href={wmPfad(o)} className="gd-karte__link">
        {!klein && (
          <div className="gd-karte__bild">
            <BildImg src={bild ?? WM_BILD} ersatz={bild ? WM_BILD : null} alt="" icon={wmIcon(o)} fokus={ortBildFokus(o)} />
            {bild && o.bild_attribution && <span className="gd-karte__credit">Foto: {o.bild_attribution}</span>}
          </div>
        )}
        <div className="gd-karte__text">
          <span className="gd-typ"><Icon name={wmIcon(o)} />{rolleText(o)}</span>
          <h3 className="gd-karte__name d">{o.name}</h3>
          <span className="gd-karte__meta">
            {o.stadtteil && <span className="gd-karte__ort"><Icon name="location_on" />{stadtteilName(o.stadtteil)}</span>}
            {s && <span className="gd-karte__ort"><Icon name="date_range" />{datumKurz(s.von)} bis {datumKurz(s.bis)}</span>}
          </span>
          <WmZustandZeile o={o} tag={tag} />
          <BadgeListe liste={badges(o, alle)} />
        </div>
      </Link>
    </article>
  );
}
