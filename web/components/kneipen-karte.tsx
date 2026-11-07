// Card für Kneipen & Bars (Design-Handoff v2, Ansicht 18): Typ-Label KNEIPE/BAR, Spezialitäten-Zeile,
// Happy-Hour-Badge (nur belegt), danach max. 2 Vibe-Chips (ohne Badge max. 3).
import Link from "next/link";
import { BildImg } from "./client";
import { Icon } from "./karten";
import { Bewertung, ortPfad } from "./ort-karten";
import { artInfo, happyHour, spezialitaeten, vibes } from "@/lib/kneipen";
import { ortBildUrl } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

export function KneipenKarte({ o }: { o: DddOrt }) {
  const bild = ortBildUrl(o);
  const art = artInfo(o);
  const spez = spezialitaeten(o);
  const hh = happyHour(o);
  const chips = vibes(o).slice(0, hh ? 2 : 3);
  return (
    <article className="gd-karte gd-karte--abend" role="listitem">
      <Link href={ortPfad(o)} className="gd-karte__link">
        <div className="gd-karte__bild">
          {/* Name steht im selben Link – Bild ist dekorativ */}
          <BildImg src={bild} alt="" icon={art.icon} />
          {o.preis_niveau && <span className="gd-karte__preis">{o.preis_niveau}</span>}
          {bild && o.bild_attribution && <span className="gd-karte__credit">Foto: {o.bild_attribution}</span>}
        </div>
        <div className="gd-karte__text">
          <span className="gd-typ gd-typ--abend"><Icon name={art.icon} />{art.label}</span>
          <h3 className="gd-karte__name d">{o.name}</h3>
          {spez.length > 0 && <span className="gd-karte__spez"><Icon name="local_bar" />{spez.join(" · ")}</span>}
          <span className="gd-karte__meta">
            {o.stadtteil && <span className="gd-karte__ort"><Icon name="location_on" />{o.stadtteil}</span>}
            {o.stadtteil && o.google_rating != null && <span className="gd-trenner" aria-hidden />}
            <Bewertung o={o} />
          </span>
          {(hh || chips.length > 0) && (
            <span className="gd-karte__tags">
              {hh && <span className="gd-hh"><Icon name="schedule" />Happy Hour {hh}</span>}
              {chips.map((v) => <span key={v} className="gd-tag">{v}</span>)}
            </span>
          )}
        </div>
      </Link>
    </article>
  );
}
