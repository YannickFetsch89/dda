// Darstellungs-Komponenten für Orte (Restaurants, Cafés etc.)
import Link from "next/link";
import { BildImg } from "./client";
import { Icon } from "./karten";
import type { DddOrt } from "@/lib/typen";

/** URL-Pfad zur Detailseite eines Ortes. */
export function ortPfad(o: DddOrt): string {
  const route = ortRoute(o.typ);
  return `/${route}/${encodeURIComponent(o.slug)}`;
}

/** Basis-Route für einen Ort-Typ. */
function ortRoute(typ: string): string {
  switch (typ) {
    case "restaurant":
    case "cafe":
      return "restaurants";
    case "kneipe":
      return "kneipen";
    case "club":
      return "clubs";
    case "spielplatz":
      return "spielplaetze";
    case "ausflug":
      return "ausfluege";
    case "wochenendtipp":
      return "wochenendtipps";
    default:
      return "restaurants";
  }
}

const TYP_ICON: Record<string, string> = {
  restaurant: "restaurant",
  cafe: "local_cafe",
  kneipe: "sports_bar",
  club: "nightlife",
  spielplatz: "toys",
  ausflug: "hiking",
  wochenendtipp: "luggage",
};

function typIcon(typ: string): string {
  return TYP_ICON[typ] ?? "place";
}

function typLabel(typ: string): string {
  switch (typ) {
    case "restaurant": return "Restaurant";
    case "cafe": return "Café";
    case "kneipe": return "Kneipe";
    case "club": return "Club";
    case "spielplatz": return "Spielplatz";
    case "ausflug": return "Ausflug";
    case "wochenendtipp": return "Wochenendtipp";
    default: return typ;
  }
}

export function OrtKarte({ o }: { o: DddOrt }) {
  return (
    <article className="ort-karte" role="listitem">
      <Link href={ortPfad(o)} className="ort-karte__link">
        <div className="ort-karte__bild">
          <BildImg src={o.bild_url} alt={o.name} icon={typIcon(o.typ)} />
          {o.preis_niveau && <span className="ort-karte__preis">{o.preis_niveau}</span>}
        </div>
        <div className="ort-karte__text">
          <span className="ort-karte__typ">
            <Icon name={typIcon(o.typ)} /> {typLabel(o.typ)}
          </span>
          <h3 className="ort-karte__name">{o.name}</h3>
          {o.untertitel && <p className="ort-karte__sub">{o.untertitel}</p>}
          <span className="ort-karte__meta">
            {o.stadtteil && <span><Icon name="location_on" /> {o.stadtteil}</span>}
            {o.google_rating != null && (
              <span className="ort-karte__rating">
                <Icon name="star" /> {o.google_rating.toFixed(1)}
                {o.google_bewertungen_anzahl != null && (
                  <span className="ort-karte__anz"> ({o.google_bewertungen_anzahl})</span>
                )}
              </span>
            )}
          </span>
          {o.tags.length > 0 && (
            <div className="ort-karte__tags">
              {o.tags.slice(0, 4).map((t) => <span key={t} className="chip chip--klein">{t}</span>)}
            </div>
          )}
        </div>
      </Link>
    </article>
  );
}

export function OrtKartenGrid({ orte }: { orte: DddOrt[] }) {
  if (!orte.length) {
    return (
      <div className="leer">
        <Icon name="restaurant" />
        <p>Noch keine Einträge vorhanden.</p>
        <p style={{ fontSize: 14, color: "var(--ddd-text-muted)" }}>
          Wir arbeiten daran – bald findest du hier kuratierte Empfehlungen!
        </p>
      </div>
    );
  }
  return (
    <div className="ort-grid" role="list">
      {orte.map((o) => <OrtKarte key={o.id} o={o} />)}
    </div>
  );
}
