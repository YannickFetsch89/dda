// Card für den Club-Hub (Design-Handoff v2, Ansicht 22): Genre-Badge oben links, Eintritts-Badge oben rechts,
// Name, „Stadtteil · Genres“, darunter das nächste Event aus dem Kalender (eigener Link, nicht verschachtelt).
import Link from "next/link";
import { BildImg } from "./client";
import { Icon, eventPfad } from "./karten";
import { clubArtInfo, clubStufe, hauptGenres, istSichtbarerClub } from "@/lib/clubs";
import { tagKurz } from "@/lib/datum";
import { ortBildFokus, ortBildUrl } from "@/lib/orte";
import type { DddEvent, DddOrt } from "@/lib/typen";

/** Pfad im Club-Hub – auch für Orte, deren Haupt-URL in einem anderen Hub liegt (auch_club). */
export const clubPfad = (o: DddOrt) => `/guides/clubs/${encodeURIComponent(o.slug)}`;

export function ClubKarte({ o, naechstes }: { o: DddOrt; naechstes?: DddEvent | null }) {
  const bild = ortBildUrl(o);
  const art = clubArtInfo(o);
  const genres = hauptGenres(o);
  const top = clubStufe(o) === "a";
  return (
    <article className="cl-karte" role="listitem">
      <Link href={clubPfad(o)} className="cl-karte__link">
        <div className="cl-karte__bild">
          {/* Name steht im selben Link – Bild ist dekorativ */}
          <BildImg src={bild} alt="" icon={art.icon} fokus={ortBildFokus(o)} />
          {/* Genre und ggf. „Top-Empfehlung“ – Preis-Badges sind auf Wunsch entfernt (Eintritt steht auf der Detailseite) */}
          {(genres[0] || top) && (
            <span className="cl-badges">
              {genres[0] && <span className="cl-genre">{genres[0]}</span>}
              {top && <span className="cl-eintritt cl-top"><Icon name="star" />Top</span>}
            </span>
          )}
          {bild && o.bild_attribution && <span className="gd-karte__credit">Foto: {o.bild_attribution}</span>}
        </div>
        <div className="cl-karte__text">
          <span className="cl-karte__art"><Icon name={art.icon} />{art.label}</span>
          <h3 className="cl-karte__name d">{o.name}</h3>
          <span className="cl-karte__meta">
            <Icon name="location_on" />
            {[o.stadtteil, genres.slice(0, 3).join(" / ")].filter(Boolean).join(" · ")}
          </span>
        </div>
      </Link>
      {naechstes && (
        <div className="cl-karte__event">
          <Icon name="event" />
          <span className="muted">Nächstes Event:</span>
          <Link href={eventPfad(naechstes)} className="cl-karte__eventlink">
            {tagKurz(naechstes.datum)} – {naechstes.titel}
          </Link>
        </div>
      )}
    </article>
  );
}

/** Auf Kneipen-/Restaurant-Seiten: Hinweis aufs Club-Profil (Musik, Partyreihen) für Orte mit auch_club. */
export function ClubProfilLink({ o }: { o: DddOrt }) {
  if (!istSichtbarerClub(o)) return null;
  const genres = hauptGenres(o).slice(0, 2).join(" · ");
  return (
    <Link href={clubPfad(o)} className="gd-knopf">
      <Icon name="nightlife" />Club-Profil{genres && <span className="gd-knopf__zusatz muted">{genres}</span>}
    </Link>
  );
}
