// Guide-Detail Club (Design-Handoff v2, Ansicht 24; Plan docs/plan-clubs-2026-11-11.md)
// Name, Profil und Adresse stehen außerhalb jeder Suspense-Grenze (erste HTML-Antwort);
// Öffnungszeiten (Wochentag), nächste Events und ähnliche Clubs werden nachgeladen.
// Orte mit Haupt-URL in einem anderen Hub (auch_club, z. B. Pitcher) haben hier eine Club-Ansicht mit
// Canonical auf die Haupt-URL und noindex – jede Seite erscheint so nur einmal im Index.
export const instant = false;
import { guideStadtteilPfad } from "@/lib/landing";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { BeschreibungText } from "@/components/beschreibung-text";
import { BildImg, GoogleKarte, Reihe } from "@/components/client";
import { ClubKarte } from "@/components/club-karte";
import { EventKarte, Icon } from "@/components/karten";
import { InfoZeile, Oeffnungszeiten, domain } from "@/components/ort-detail";
import { ortPfad } from "@/components/ort-karten";
import { kurzBeschreibung } from "@/lib/beschreibung";
import {
  FAKT_LABEL, alleGenres, clubArtInfo, clubBeschreibung, clubHighlight, clubProfil, clubScore, clubsSortieren,
  eintrittKurz, genreIcon, genreSlug, hauptGenres,
} from "@/lib/clubs";
import { clubLaden, clubsLaden, naechsteEvents } from "@/lib/clubs-daten";
import { clubJsonLd, clubKanonischerPfad } from "@/lib/clubs-json-ld";
import { eventPoolLaden } from "@/lib/daten";
import { tagLang } from "@/lib/datum";
import { sterne, zahl } from "@/lib/guide-filter";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { jsonLdText } from "@/lib/json-ld";
import { ortBildAutorUrl, ortBildFokus, ortBildUrl, sichereUrl, slugDekodieren } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

const BASIS = "/guides/clubs";
const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type Props = { params: Promise<{ slug: string }> };

async function laden(props: Props): Promise<DddOrt | null> {
  const slug = slugDekodieren((await props.params).slug);
  return slug ? clubLaden(slug) : null;
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const ort = await laden(props);
  if (!ort) return { title: "Nicht gefunden" };
  const art = clubArtInfo(ort).label;
  const genres = hauptGenres(ort).slice(0, 3).join(", ");
  const titel = `${ort.name} – ${art} in ${ort.stadtteil ?? "Düsseldorf"}${genres ? ` (${genres})` : ""}`;
  const beschreibung =
    kurzBeschreibung(clubBeschreibung(ort), 160) ?? `${ort.name}: ${art} in ${ort.stadtteil ?? "Düsseldorf"}. Empfohlen von dies.das.düsseldorf.`;
  const eigene = ort.typ === "club";
  const pfad = eigene ? `${BASIS}/${encodeURIComponent(ort.slug)}` : ortPfad(ort);
  const bild = ortBildUrl(ort);
  return {
    title: titel,
    description: beschreibung,
    alternates: { canonical: pfad },
    robots: eigene ? undefined : { index: false, follow: true },
    openGraph: { title: titel, description: beschreibung, url: pfad, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE", ...(bild ? { images: [{ url: bild }] } : {}) },
    twitter: { card: bild ? "summary_large_image" : "summary", title: titel, description: beschreibung, ...(bild ? { images: [bild] } : {}) },
  };
}

async function NaechsteEvents({ ort }: { ort: DddOrt }) {
  const pool = await eventPoolLaden();
  const events = naechsteEvents(ort, pool, 10);
  if (!events.length) return null;
  return (
    <section className="gd-abschnitt">
      <div className="gd-abschnitt__kopf">
        <h2 className="d">Nächste Events hier</h2>
        <Link href={`/entdecken?q=${encodeURIComponent(ort.name)}`} className="link">Alle Events</Link>
      </div>
      <p className="muted cl-unterzeile">Aus unserem Eventkalender, gefiltert nach „{ort.name}“</p>
      <Reihe breite={258} label={`Events im ${ort.name}`}>
        {events.map((e) => <EventKarte key={e.id} e={e} heute={pool.heute} variante="reihe" />)}
      </Reihe>
    </section>
  );
}

async function AehnlicheClubs({ ort }: { ort: DddOrt }) {
  const eigene = new Set(alleGenres(ort));
  const [alle, pool] = await Promise.all([clubsLaden(), eventPoolLaden()]);
  const andere = clubsSortieren(alle, "empfohlen").filter((o) => o.id !== ort.id);
  // Erst gleiches Hauptgenre, dann irgendein gemeinsames Genre, dann gleicher Stadtteil
  const haupt = hauptGenres(ort)[0];
  const auswahl = [
    ...new Map(
      [
        ...andere.filter((o) => haupt && hauptGenres(o).includes(haupt)),
        ...andere.filter((o) => alleGenres(o).some((g) => eigene.has(g))),
        ...andere.filter((o) => o.stadtteil === ort.stadtteil),
      ].map((o) => [o.id, o]),
    ).values(),
  ].slice(0, 3);
  if (!auswahl.length) return null;
  return (
    <section className="gd-abschnitt">
      <div className="gd-abschnitt__kopf">
        <h2 className="d">Ähnliche Clubs</h2>
        <Link href={BASIS} className="link">Alle Clubs</Link>
      </div>
      <div className="cl-grid" role="list">
        {auswahl.map((o) => <ClubKarte key={o.id} o={o} naechstes={naechsteEvents(o, pool, 1)[0]} />)}
      </div>
    </section>
  );
}

/** Teilwerte des Club-Scores als Balken (transparent: woraus sich die Empfehlung ergibt). */
function ScorePanel({ ort }: { ort: DddOrt }) {
  const s = clubScore(ort);
  if (!s) return null;
  const teile = [
    { label: "Programm", wert: s.programm, hilfe: "Events in unserem Kalender, feste Reihen" },
    { label: "Szene", wert: s.szene, hilfe: "Kuratierte Line-ups, Reihen, Kulturprogramm" },
    { label: "Profil", wert: s.profil, hilfe: "Belegte Musik, Reihen und Infos" },
    { label: "Beliebtheit", wert: s.beliebtheit, hilfe: "Google-Bewertungen (schwach gewichtet)" },
  ];
  return (
    <div className="cl-score">
      <div className="cl-score__kopf">
        <h2>Club-Score</h2>
        <span className="cl-score__wert">{s.gesamt}<small>/10</small></span>
      </div>
      {teile.map((t) => (
        <div key={t.label} className="cl-score__zeile" title={t.hilfe}>
          <span>{t.label}</span>
          <span className="cl-score__balken" aria-hidden><span style={{ width: `${Math.max(4, t.wert * 10)}%` }} /></span>
          <b>{t.wert.toLocaleString("de-DE")}</b>
        </div>
      ))}
    </div>
  );
}

export default async function ClubDetail(props: Props) {
  const ort = await laden(props);
  if (!ort) notFound();

  const profil = clubProfil(ort)!;
  const art = clubArtInfo(ort);
  const bild = ortBildUrl(ort);
  const autorUrl = ortBildAutorUrl(ort);
  const webseite = sichereUrl(ort.webseite);
  const kartenAdresse = [ort.name, ort.adresse ?? `${ort.stadtteil ?? ""} Düsseldorf`.trim()].join(", ");
  const routeUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(
    ort.latitude != null && ort.longitude != null ? `${ort.latitude},${ort.longitude}` : kartenAdresse,
  )}`;
  const [strasse, ...ortTeil] = (ort.adresse ?? "").split(", ");
  const haupt = profil.genres.filter((g) => g.anteil === "haupt").map((g) => g.wert);
  const neben = profil.genres.filter((g) => g.anteil !== "haupt").map((g) => g.wert);
  const pill = (haupt.length ? haupt : neben).slice(0, 2);
  const eintritt = eintrittKurz(ort);
  const typZeile = [art.label, ort.stadtteil].filter(Boolean).join(" · ");
  const highlight = clubHighlight(ort);
  // Brotkrumen zeigen auf dieselbe URL wie das Canonical (bei auch_club die Haupt-URL im anderen Hub)
  const pfad = clubKanonischerPfad(ort);
  const jsonLd = [
    clubJsonLd(ort, SITE_URL),
    brotkrumenJsonLd(SITE_URL, [
      { name: "Start", pfad: "/" },
      { name: "Clubs", pfad: BASIS },
      { name: ort.name, pfad },
    ]),
  ];
  // Info-Panel: belegte Fakten aus dem Profil (Eintritt als Spanne, sonst Text)
  const fakten = Object.entries(profil.fakten).filter(([k]) => k !== "eintritt" && k !== "oeffnung");

  return (
    <div className="container gd-detail gd-seite gd-seite--abend cl-seite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link><span>/</span>
        <Link href={BASIS}>Clubs</Link><span>/</span>
        <span aria-current="page">{ort.name}</span>
      </nav>

      {bild && (
        <div className="gd-detail__hero cl-detail__hero">
          <BildImg src={bild} alt={`${ort.name}, ${art.label} in ${ort.stadtteil ?? "Düsseldorf"}`} icon={art.icon} eager fokus={ortBildFokus(ort)} />
          {ort.bild_attribution && (
            <span className="gd-detail__credit">
              Foto:{" "}
              {autorUrl ? <a href={autorUrl} target="_blank" rel="noopener noreferrer">{ort.bild_attribution}</a> : ort.bild_attribution}
            </span>
          )}
        </div>
      )}

      <div className="gd-detail__spalten">
        <div className="gd-detail__haupt">
          <span className="gd-typ gd-typ--gross gd-typ--abend"><Icon name={art.icon} />{typZeile}</span>
          <div className="cl-titel">
            <h1 className="d">{ort.name}</h1>
            {pill.length > 0 && (
              <span className="cl-pill"><Icon name={genreIcon(pill[0])} />{pill.join(" · ")}</span>
            )}
          </div>
          {highlight && <blockquote className="gd-zitat">{highlight}</blockquote>}
          <BeschreibungText text={clubBeschreibung(ort)} />

          {profil.genres.length > 0 && (
            <section className="cl-block">
              <h2 className="d">Musik</h2>
              {haupt.length > 0 && (
                <div className="cl-block__zeile">
                  <span className="muted">Hauptsächlich</span>
                  <div className="cl-chips">
                    {haupt.map((g) => (
                      <Link key={g} href={`${BASIS}?genre=${genreSlug(g)}`} className="cl-chip cl-chip--haupt"><Icon name={genreIcon(g)} />{g}</Link>
                    ))}
                  </div>
                </div>
              )}
              {neben.length > 0 && (
                <div className="cl-block__zeile">
                  <span className="muted">{haupt.length ? "Ab und zu" : "Gespielt wird"}</span>
                  <div className="cl-chips">
                    {neben.map((g) => (
                      <Link key={g} href={`${BASIS}?genre=${genreSlug(g)}`} className="cl-chip"><Icon name={genreIcon(g)} />{g}</Link>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {profil.formate.length > 0 && (
            <section className="cl-block">
              <h2 className="d">Reihen &amp; Partys</h2>
              <ul className="cl-formate">
                {profil.formate.map((f) => (
                  <li key={f.name}>
                    <b>{f.name}</b>
                    {(f.rhythmus || f.musik) && <span className="muted">{[f.rhythmus, f.musik].filter(Boolean).join(" · ")}</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {profil.zusatz.length > 0 && (
            <section className="cl-block">
              <h2 className="d">Was hier sonst passiert</h2>
              <ul className="cl-formate">
                {profil.zusatz.map((z) => (
                  <li key={z.art}>
                    <b>{z.art}</b>
                    {z.beispiel && <span className="muted">{z.beispiel}</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {(profil.publikum.length > 0 || profil.ausstattung.length > 0) && (
            <div className="gd-detail__tags">
              {[...profil.publikum, ...profil.ausstattung].map((t) => <span key={t} className="gd-tag gd-tag--gross">{t}</span>)}
            </div>
          )}
          <p className="cl-hinweis muted">
            Angaben aus {profil.datum ? `dem Stand vom ${tagLang(profil.datum, true)}` : "Recherche"}: Website des Clubs,
            Stadtmagazine, Google und unser Eventkalender – jede Angabe mit Quelle geprüft. Änderungen vorbehalten.
          </p>
        </div>

        <aside className="gd-detail__seite">
          <div className="gd-info">
            <h2>Infos</h2>
            {pill.length > 0 && <InfoZeile icon="graphic_eq" l1={[...haupt, ...neben].slice(0, 4).join(", ")} l2="Musikrichtung" />}
            {profil.fakten.oeffnung && <InfoZeile icon="nightlife" l1={profil.fakten.oeffnung} l2="Geöffnet" />}
            {!profil.fakten.oeffnung && ort.oeffnungszeiten && (
              <Suspense fallback={<InfoZeile icon="schedule" l1="Öffnungszeiten" />}>
                <Oeffnungszeiten text={ort.oeffnungszeiten} />
              </Suspense>
            )}
            {(eintritt || profil.fakten.eintritt) && <InfoZeile icon="confirmation_number" l1={eintritt ?? profil.fakten.eintritt} l2={eintritt && profil.fakten.eintritt ? profil.fakten.eintritt : "Eintritt"} />}
            {profil.dresscode && <InfoZeile icon="checkroom" l1={profil.dresscode} l2="Dresscode" />}
            {fakten.map(([k, v]) => <InfoZeile key={k} icon={k === "tuer" ? "door_front" : k === "alter" ? "badge" : "groups"} l1={v} l2={FAKT_LABEL[k]} />)}
            {ort.adresse && <InfoZeile icon="location_on" l1={strasse} l2={ortTeil.join(", ") || undefined} />}
            {ort.google_rating != null && (
              <InfoZeile
                icon="star"
                l1={`${sterne(ort.google_rating)} von 5`}
                l2={ort.google_bewertungen_anzahl != null ? `${zahl(ort.google_bewertungen_anzahl)} Google-Bewertungen` : undefined}
              />
            )}
          </div>
          <ScorePanel ort={ort} />
          {webseite && (
            <a href={webseite} target="_blank" rel="noopener" className="gd-knopf gd-knopf--navy">
              <Icon name="language" />Website<span className="gd-knopf__zusatz">{domain(webseite)}</span>
            </a>
          )}
          {profil.instagram && (
            <a href={profil.instagram} target="_blank" rel="noopener" className="gd-knopf">
              <Icon name="photo_camera" />Instagram
            </a>
          )}
          {profil.residentAdvisor && (
            <a href={profil.residentAdvisor} target="_blank" rel="noopener" className="gd-knopf">
              <Icon name="headphones" />Resident Advisor
            </a>
          )}
          {ort.typ !== "club" && (
            <Link href={ortPfad(ort)} className="gd-knopf">
              <Icon name="arrow_forward" />Mehr zu {ort.name}
            </Link>
          )}
          <GoogleKarte adresse={kartenAdresse} routeUrl={routeUrl} />
          {ort.stadtteil && (
            <Link href={guideStadtteilPfad("clubs", ort.stadtteil)} className="link">Mehr Clubs in {ort.stadtteil}</Link>
          )}
        </aside>
      </div>

      <Suspense fallback={null}>
        <NaechsteEvents ort={ort} />
      </Suspense>
      <Suspense fallback={null}>
        <AehnlicheClubs ort={ort} />
      </Suspense>
    </div>
  );
}
