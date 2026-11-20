// Ortsseite /orte/<slug> (Plan docs/plan-locations-2026-11-18.md, 3.6, 3.8–3.11, 3.13)
// Haus oder Saal/Standort/Filiale. Echte Statuscodes kommen aus dem Proxy (lib/pfad-pruefung.ts): Diese Seite rendert
// nur aktive Spielstätten; ein unbekannter Slug, den der Proxy wegen eines Netzfehlers durchgelassen hat, zeigt
// „Ort nicht gefunden“ (noindex), ein Abfragefehler „Gerade nicht verfügbar“ (noindex, nur kurz gecacht).
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BeschreibungText } from "@/components/beschreibung-text";
import { BildImg } from "@/components/client";
import { GuideKarteLazy } from "@/components/guide-karte-lazy";
import { EventKarte, Icon } from "@/components/karten";
import { InfoZeile, domain } from "@/components/ort-detail";
import { ortPfad } from "@/components/ort-karten";
import { kurzBeschreibung } from "@/lib/beschreibung";
import { clubKanonischerPfad } from "@/lib/clubs-json-ld";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { jsonLdText } from "@/lib/json-ld";
import { lokalesBild, ortBildFokus, sichereUrl, slugDekodieren } from "@/lib/orte";
import { ROBOTS_INDEX, seitenAlternates } from "@/lib/seo";
import {
  ORTE_BASIS, artInfo, artVon, entfernung, indexierbar, ortSeitePfad, profil, stadtVon,
} from "@/lib/spielstaetten";
import {
  kinderVon, ortZeileLaden, programmLaden, spielstaetteLaden, spielstaettenLaden, type Spielstaette,
} from "@/lib/spielstaetten-daten";
import { spielstaetteJsonLd } from "@/lib/spielstaetten-json-ld";
import type { DddEvent, DddOrt } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type Props = { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };

/** Kanonische URL eines Hauses: Spielstätte → /orte, Guide-Zeile → ihre kanonische Guide-Seite. */
function hausPfad(h: DddOrt): string {
  if (h.typ === "spielstaette") return ortSeitePfad(h.slug);
  if (h.typ === "club" || h.extras.auch_club) return clubKanonischerPfad(h);
  return ortPfad(h);
}

interface Stand {
  ort: Spielstaette;
  haus: DddOrt | null;
  kinder: Spielstaette[];
  alle: Spielstaette[];
  ids: string[];
}

async function laden(props: Props): Promise<{ stand: Stand | null; fehler: boolean }> {
  const slug = slugDekodieren((await props.params).slug);
  if (!slug) return { stand: null, fehler: false };
  const [{ ort, fehler }, liste] = await Promise.all([spielstaetteLaden(slug), spielstaettenLaden()]);
  if (!ort) return { stand: null, fehler };
  const haus = ort.parentId ? await ortZeileLaden(ort.parentId) : null;
  const kinder = kinderVon(ort.id, liste.orte);
  // Eine Abfrage je Haus (Plan 3.9): Säle laden das Programm ihres Hauses und filtern daraus
  const hausId = haus?.id ?? ort.id;
  const ids = [hausId, ...kinderVon(hausId, liste.orte).map((k) => k.id)].sort();
  return { stand: { ort, haus, kinder, alle: liste.orte, ids }, fehler: false };
}

function eigeneEvents(stand: Stand, events: DddEvent[], saal: string | null): DddEvent[] {
  if (stand.ort.parentId) return events.filter((e) => e.ort_id === stand.ort.id);
  if (saal === "haus") return events.filter((e) => e.ort_id === stand.ort.id);
  if (saal) return events.filter((e) => e.ort_id === saal);
  return events;
}

function adresseBestaetigt(stand: Stand): boolean {
  if (profil(stand.ort).adresseBestaetigt) return true;
  // Säle erben vom Haus (Plan 3.6): bestätigte Spielstätten-Adresse oder die Adresse einer Guide-Zeile
  const h = stand.haus;
  return !!h && (h.typ === "spielstaette" ? profil(h).adresseBestaetigt : !!h.adresse);
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { stand, fehler } = await laden(props);
  if (!stand) return { title: fehler ? "Gerade nicht verfügbar" : "Ort nicht gefunden", robots: { index: false, follow: true } };
  const { ort, haus } = stand;
  const p = profil(ort);
  const programm = await programmLaden(stand.ids);
  const kommende = eigeneEvents(stand, programm.events, null).length;
  const stadt = stadtVon(haus ?? ort) ?? "Düsseldorf";
  // Stadt nur anhängen, wenn sie nicht schon im Namen steht („Tonhalle Düsseldorf“)
  const titel = `${ort.name}${ort.name.includes(stadt) ? "" : ` ${stadt}`}: Programm & Infos`;
  const art = artInfo(artVon(ort, haus)).wert;
  const beschreibung = (p.textFreigegeben && kurzBeschreibung(ort.beschreibung, 160)) ||
    `${ort.name} (${art}) in ${ort.stadtteil ?? stadt}: ${kommende ? `${kommende} kommende Termine` : "Programm"}, Adresse und Infos bei dies.das.düsseldorf.`;
  const indexiert = !programm.fehler && indexierbar({
    adresseBestaetigt: adresseBestaetigt(stand), textFreigegeben: p.textFreigegeben, kommende,
  });
  const pfad = ortSeitePfad(ort.slug);
  const bild = lokalesBild(ort.bild_url);
  return {
    title: titel,
    description: beschreibung,
    alternates: seitenAlternates(pfad),
    robots: indexiert ? ROBOTS_INDEX : { index: false, follow: true },
    openGraph: { title: titel, description: beschreibung, url: pfad, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE", ...(bild ? { images: [{ url: bild }] } : {}) },
  };
}

/** Bild (nur lokal, Plan 3.13) mit Nachweis – sonst Ersatzkachel: Art-Symbol, Farbe, Name. Nie ein Google-Foto. */
function Kopfbild({ ort, art }: { ort: DddOrt; art: string | null }) {
  const lokal = lokalesBild(ort.bild_url);
  const version = ort.extras.foto_version;
  const src = lokal ? `${lokal}${typeof version === "number" && version > 1 ? `?v=${version}` : ""}` : null;
  const info = artInfo(art);
  if (!src) {
    return (
      <div className={`os-kachel os-kachel--${info.slug}`} aria-hidden>
        <Icon name={info.icon} />
        <span>{ort.name}</span>
      </div>
    );
  }
  const link = sichereUrl(ort.extras.bild_link);
  return (
    <div className="gd-detail__hero">
      <BildImg src={src} alt={`${ort.name} in Düsseldorf`} icon={info.icon} eager fokus={ortBildFokus(ort)} />
      {ort.bild_attribution && (
        <span className="gd-detail__credit">
          Foto: {link?.startsWith("https://") ? <a href={link} target="_blank" rel="noopener noreferrer">{ort.bild_attribution}</a> : ort.bild_attribution}
        </span>
      )}
    </div>
  );
}

async function Programm({ stand, searchParams }: { stand: Stand; searchParams: Props["searchParams"] }) {
  const sp = await searchParams;
  const saalRoh = typeof sp.saal === "string" ? sp.saal : null;
  const saal = saalRoh && (saalRoh === "haus" || stand.kinder.some((k) => k.id === saalRoh)) ? saalRoh : null;
  const programm = await programmLaden(stand.ids);
  if (programm.fehler) {
    return (
      <section className="gd-abschnitt">
        <h2 className="d">Programm</h2>
        <p className="muted">Programm gerade nicht verfügbar. Bitte später noch einmal versuchen.</p>
      </section>
    );
  }
  const events = eigeneEvents(stand, programm.events, saal);
  const laeufer = events.filter((e) => e.datum_bis && e.datum_bis > e.datum);
  const termine = events.filter((e) => !(e.datum_bis && e.datum_bis > e.datum));
  const pfad = ortSeitePfad(stand.ort.slug);
  return (
    <section className="gd-abschnitt" id="programm">
      <div className="gd-abschnitt__kopf">
        <h2 className="d">Nächste Events</h2>
        <span className="muted">{events.length ? `${events.length} Termine` : ""}</span>
      </div>
      {stand.kinder.length > 0 && !stand.ort.parentId && (
        <nav className="os-saele" aria-label="Nach Saal filtern">
          <Link href={`${pfad}#programm`} className={`gd-chip${!saal ? " gd-chip--an" : ""}`} scroll={false}>Alle</Link>
          {stand.kinder.map((k) => (
            <Link key={k.id} href={`${pfad}?saal=${k.id}#programm`} className={`gd-chip${saal === k.id ? " gd-chip--an" : ""}`} scroll={false}>
              {k.name.replace(`${stand.ort.name} – `, "")}
            </Link>
          ))}
          <Link href={`${pfad}?saal=haus#programm`} className={`gd-chip${saal === "haus" ? " gd-chip--an" : ""}`} scroll={false}>Haus allgemein</Link>
        </nav>
      )}
      {laeufer.length > 0 && (
        <>
          <h3 className="os-unterkopf">Läuft gerade</h3>
          <div className="raster" role="list">
            {laeufer.map((e) => <EventKarte key={e.id} e={e} heute={programm.heute} variante="grid" />)}
          </div>
        </>
      )}
      {termine.length > 0 ? (
        <div className="raster" role="list">
          {termine.slice(0, 60).map((e) => <EventKarte key={e.id} e={e} heute={programm.heute} variante="grid" />)}
        </div>
      ) : (
        !laeufer.length && <p className="muted">Gerade keine kommenden Termine in unserem Kalender.</p>
      )}
      {termine.length > 60 && <p className="muted">… und {termine.length - 60} weitere Termine.</p>}
    </section>
  );
}

async function Reihen({ stand }: { stand: Stand }) {
  const programm = await programmLaden(stand.ids);
  const reihen = [...new Map(eigeneEvents(stand, programm.events, null).filter((e) => e.reihe).map((e) => [e.reihe!.slug, e.reihe!])).values()];
  if (!reihen.length) return null;
  return (
    <section className="gd-abschnitt">
      <h2 className="d">Reihen an diesem Ort</h2>
      <ul className="os-liste">
        {reihen.slice(0, 12).map((r) => <li key={r.slug}><Link href={`/reihe/${encodeURIComponent(r.slug)}`}>{r.titel}</Link></li>)}
      </ul>
    </section>
  );
}

// `punkt`: eigene Koordinaten, sonst die des Hauses (Säle haben meist keine eigenen)
function AehnlicheOrte({ stand, art, punkt }: { stand: Stand; art: string | null; punkt: { lat: number; lng: number } | null }) {
  const ich = stand.ort;
  const haeuser = stand.alle.filter((o) => !o.parentId && o.id !== ich.id && o.id !== stand.haus?.id);
  const nah = punkt
    ? haeuser.filter((o) => o.latitude != null && o.longitude != null)
      .map((o) => ({ o, m: entfernung(punkt, { lat: o.latitude!, lng: o.longitude! }) }))
      .sort((a, b) => a.m - b.m).slice(0, 4)
    : [];
  const gleich = haeuser.filter((o) => art && profil(o).art === art && !nah.some((n) => n.o.id === o.id)).slice(0, 4);
  if (!nah.length && !gleich.length) return null;
  return (
    <section className="gd-abschnitt">
      <h2 className="d">Weitere Orte</h2>
      <div className="os-spalten">
        {nah.length > 0 && (
          <div>
            <h3 className="os-unterkopf">In der Nähe</h3>
            <ul className="os-liste">
              {nah.map(({ o, m }) => (
                <li key={o.id}><Link href={ortSeitePfad(o.slug)}>{o.name}</Link> <span className="muted">· {m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toLocaleString("de-DE", { maximumFractionDigits: 1 })} km`}</span></li>
              ))}
            </ul>
          </div>
        )}
        {gleich.length > 0 && (
          <div>
            <h3 className="os-unterkopf">{artInfo(art).wert}</h3>
            <ul className="os-liste">
              {gleich.map((o) => <li key={o.id}><Link href={ortSeitePfad(o.slug)}>{o.name}</Link>{o.stadtteil && <span className="muted"> · {o.stadtteil}</span>}</li>)}
            </ul>
          </div>
        )}
      </div>
      <Link href={ORTE_BASIS} className="link">Alle Orte</Link>
    </section>
  );
}

async function JsonLd({ stand, art }: { stand: Stand; art: string | null }) {
  const programm = await programmLaden(stand.ids);
  const pfad = ortSeitePfad(stand.ort.slug);
  const daten = [
    spielstaetteJsonLd(stand.ort.parentId && stand.haus ? { ...stand.ort, adresse: stand.ort.adresse ?? stand.haus.adresse, latitude: stand.ort.latitude ?? stand.haus.latitude, longitude: stand.ort.longitude ?? stand.haus.longitude } : stand.ort,
      art, SITE_URL, pfad, stand.haus ? { name: stand.haus.name, pfad: hausPfad(stand.haus) } : null,
      programm.fehler ? [] : eigeneEvents(stand, programm.events, null), adresseBestaetigt(stand)),
    brotkrumenJsonLd(SITE_URL, [
      { name: "Start", pfad: "/" },
      { name: "Orte", pfad: ORTE_BASIS },
      ...(stand.haus ? [{ name: stand.haus.name, pfad: hausPfad(stand.haus) }] : []),
      { name: stand.ort.name, pfad },
    ]),
  ].filter(Boolean);
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(daten) }} />;
}

export default async function OrtSeite(props: Props) {
  const { stand, fehler } = await laden(props);
  if (!stand) {
    return (
      <div className="container gd-seite">
        <h1 className="d">{fehler ? "Gerade nicht verfügbar" : "Ort nicht gefunden"}</h1>
        <p className="muted">{fehler ? "Die Ortsseite kann gerade nicht geladen werden. Bitte versuch es gleich noch einmal." : "Diesen Ort gibt es bei uns nicht (mehr)."}</p>
        <p><Link href={ORTE_BASIS} className="link">Alle Orte in Düsseldorf</Link></p>
      </div>
    );
  }
  const { ort, haus, kinder } = stand;
  const p = profil(ort);
  const art = artVon(ort, haus);
  const info = artInfo(art);
  // Säle erben Adresse, Koordinaten, Stadtteil und Stadt vom Haus (Plan 3.6)
  const quelle = ort.adresse ? ort : haus ?? ort;
  const stadt = stadtVon(quelle);
  const ortsangabe = quelle.stadtteil ?? stadt;
  const webseite = sichereUrl(ort.webseite ?? (haus?.webseite || null));
  const lat = ort.latitude ?? haus?.latitude ?? null;
  const lng = ort.longitude ?? haus?.longitude ?? null;
  const ziel = lat != null && lng != null ? `${lat},${lng}` : [ort.name, quelle.adresse].filter(Boolean).join(", ");
  const routeUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(ziel)}`;
  const [strasse, ...ortTeil] = (quelle.adresse ?? "").split(", ");

  return (
    <div className="container gd-detail gd-seite os-seite">
      <Suspense fallback={null}><JsonLd stand={stand} art={art} /></Suspense>
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link><span>/</span>
        <Link href={ORTE_BASIS}>Orte</Link><span>/</span>
        {haus && <><Link href={hausPfad(haus)}>{haus.name}</Link><span>/</span></>}
        <span aria-current="page">{ort.name}</span>
      </nav>

      <Kopfbild ort={ort} art={art} />

      <div className="gd-detail__spalten">
        <div className="gd-detail__haupt">
          <span className="gd-typ gd-typ--gross"><Icon name={info.icon} />{[info.wert, ortsangabe].filter(Boolean).join(" · ")}</span>
          <h1 className="d">{ort.name}</h1>
          {haus && (
            <p className="os-haus">
              {p.zeileTyp === "standort" ? "Standort von" : "Saal im Haus"} <Link href={hausPfad(haus)}>{haus.name}</Link>
            </p>
          )}
          {/* Über den Ort: nur mit freigegebenem Text (Plan 3.14); Säle wiederholen keinen Haustext (Plan 3.6) */}
          {p.textFreigegeben && ort.beschreibung && (
            <section className="cl-block">
              <h2 className="d">Über den Ort</h2>
              <BeschreibungText text={ort.beschreibung} />
            </section>
          )}
        </div>

        <aside className="gd-detail__seite">
          <div className="gd-info">
            <h2>Infos</h2>
            {quelle.adresse && <InfoZeile icon="location_on" l1={strasse} l2={ortTeil.join(", ") || undefined} />}
            {!quelle.adresse && <InfoZeile icon="location_on" l1={ortsangabe ?? "Düsseldorf"} l2="Adresse folgt" />}
            {kinder.length > 0 && (
              <InfoZeile icon="meeting_room" l1={`${kinder.length} ${p.zeileTyp === "haus" && kinder.some((k) => profil(k).zeileTyp === "standort") ? "Standorte" : "Säle mit eigener Seite"}`}>
                <ul className="os-liste os-liste--knapp">
                  {kinder.map((k) => <li key={k.id}><Link href={ortSeitePfad(k.slug)}>{k.name}</Link></li>)}
                </ul>
              </InfoZeile>
            )}
          </div>
          {webseite && (
            <a href={webseite} target="_blank" rel="noopener" className="gd-knopf gd-knopf--navy">
              <Icon name="language" />Website<span className="gd-knopf__zusatz">{domain(webseite)}</span>
            </a>
          )}
          {/* Gewöhnlicher Link, kein eingebetteter Google-Rahmen (Plan 3.8): der Browser lädt hier nichts von Dritten */}
          <a href={routeUrl} target="_blank" rel="noopener noreferrer" className="gd-knopf">
            <Icon name="directions" />Route planen
          </a>
        </aside>
      </div>

      <Suspense fallback={<section className="gd-abschnitt"><h2 className="d">Nächste Events</h2><p className="muted">Programm wird geladen …</p></section>}>
        <Programm stand={stand} searchParams={props.searchParams} />
      </Suspense>

      {lat != null && lng != null && (
        <section className="gd-abschnitt">
          <h2 className="d">Karte</h2>
          <GuideKarteLazy quelle={`/api/guide-karte?hub=orte&nahe=${encodeURIComponent(ort.slug)}&lat=${lat}&lng=${lng}`} />
        </section>
      )}

      <Suspense fallback={null}><Reihen stand={stand} /></Suspense>
      <AehnlicheOrte stand={stand} art={art} punkt={lat != null && lng != null ? { lat, lng } : null} />
    </div>
  );
}
