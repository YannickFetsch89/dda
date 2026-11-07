// Darstellungs-Komponenten für Orte (Guides) – Card nach Design-Handoff v2, Ansicht 12/14
import Link from "next/link";
import { BildImg } from "./client";
import { Icon } from "./karten";
import { kueche, sterne, zahl } from "@/lib/guide-filter";
import { artInfo } from "@/lib/kneipen";
import { ortBildUrl } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

/** Basis-Route eines Ort-Typs (Guide-Hub). */
export function ortRoute(typ: string): string {
  switch (typ) {
    case "restaurant":
    case "imbiss":
    case "cafe":
      return "/guides/restaurants-cafes";
    case "kneipe":
      return "/guides/kneipen-bars";
    case "club":
      return "/guides/clubs";
    case "spielplatz":
      return "/guides/spielplaetze";
    case "ausflug":
      return "/guides/ausfluege";
    case "wochenendtipp":
      return "/guides/wochenend-trips";
    default:
      return "/guides/restaurants-cafes";
  }
}

/** URL-Pfad zur Detailseite eines Ortes. */
export function ortPfad(o: DddOrt): string {
  return `${ortRoute(o.typ)}/${encodeURIComponent(o.slug)}`;
}

const TYP_ICON: Record<string, string> = {
  restaurant: "restaurant",
  imbiss: "lunch_dining",
  cafe: "local_cafe",
  kneipe: "sports_bar",
  club: "nightlife",
  spielplatz: "toys",
  ausflug: "hiking",
  wochenendtipp: "luggage",
};

export function typIcon(typ: string): string {
  return TYP_ICON[typ] ?? "place";
}

export function typLabel(typ: string): string {
  switch (typ) {
    case "restaurant": return "Restaurant";
    case "imbiss": return "Schnellimbiss";
    case "cafe": return "Café";
    case "kneipe": return "Kneipe";
    case "club": return "Club";
    case "spielplatz": return "Spielplatz";
    case "ausflug": return "Ausflug";
    case "wochenendtipp": return "Wochenend-Trip";
    default: return typ;
  }
}

/** Typ-Label eines Ortes: Kneipen zeigen ihre Unterart (Brauhaus, Bar, Kneipe) – auch im Restaurant-Hub. */
export function ortTypLabel(o: DddOrt): string {
  return o.typ === "kneipe" ? artInfo(o).label : typLabel(o.typ);
}

export function ortTypIcon(o: DddOrt): string {
  return o.typ === "kneipe" ? artInfo(o).icon : typIcon(o.typ);
}

/** Untertitel der Card: "Japanisch · Flingern · €€" (fehlende Teile entfallen). */
export function ortUntertitel(o: DddOrt): string {
  return [o.untertitel ?? kueche(o)?.name, o.stadtteil, o.preis_niveau].filter(Boolean).join(" · ");
}

export function Bewertung({ o }: { o: DddOrt }) {
  if (o.google_rating == null) return null;
  return (
    <span className="gd-bewertung">
      <Icon name="star" className="is-active" />
      <b>{sterne(o.google_rating)}</b>
      {o.google_bewertungen_anzahl != null && <span className="muted">({zahl(o.google_bewertungen_anzahl)})</span>}
    </span>
  );
}

export function OrtKarte({ o }: { o: DddOrt }) {
  const bild = ortBildUrl(o);
  return (
    <article className="gd-karte" role="listitem">
      <Link href={ortPfad(o)} className="gd-karte__link">
        <div className="gd-karte__bild">
          {/* Name steht im selben Link – Bild ist dekorativ */}
          <BildImg src={bild} alt="" icon={ortTypIcon(o)} />
          {o.preis_niveau && <span className="gd-karte__preis">{o.preis_niveau}</span>}
          {bild && o.bild_attribution && <span className="gd-karte__credit">Foto: {o.bild_attribution}</span>}
        </div>
        <div className="gd-karte__text">
          <span className="gd-typ"><Icon name={ortTypIcon(o)} />{ortTypLabel(o)}</span>
          <h3 className="gd-karte__name d">{o.name}</h3>
          <span className="gd-karte__sub">{ortUntertitel(o)}</span>
          <span className="gd-karte__meta">
            {o.stadtteil && <span className="gd-karte__ort"><Icon name="location_on" />{o.stadtteil}</span>}
            {o.stadtteil && o.google_rating != null && <span className="gd-trenner" aria-hidden />}
            <Bewertung o={o} />
          </span>
          {o.tags.length > 0 && (
            <span className="gd-karte__tags">
              {o.tags.slice(0, 3).map((t) => <span key={t} className="gd-tag">{t}</span>)}
            </span>
          )}
        </div>
      </Link>
    </article>
  );
}

export function OrtKartenGrid({ orte, spalten = 3 }: { orte: DddOrt[]; spalten?: 3 | 4 }) {
  return (
    <div className={`gd-grid gd-grid--${spalten}`} role="list">
      {orte.map((o) => <OrtKarte key={o.id} o={o} />)}
    </div>
  );
}
