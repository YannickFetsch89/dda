// Guide-Detail Spielplatz (Design-Handoff v2, Ansicht 25; Plan docs/plan-spielplaetze-2026-11-12.md, 5.3)
// Name, Profil und Ausstattung stehen außerhalb jeder Suspense-Grenze (erste HTML-Antwort);
// Cafés und Familien-Events in der Nähe werden nachgeladen.
// Indexierbar nur mit Profil-Beschreibung und ≥ 2 belegten Geräten (5.4), sonst noindex ohne Canonical.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { BeschreibungText } from "@/components/beschreibung-text";
import { BildImg, GoogleKarte, Reihe } from "@/components/client";
import { EventKarte, Icon } from "@/components/karten";
import { InfoZeile, Oeffnungszeiten } from "@/components/ort-detail";
import { OrtKarte } from "@/components/ort-karten";
import { AlterBadge, SpielplatzKarte } from "@/components/spielplatz-karte";
import { kurzBeschreibung } from "@/lib/beschreibung";
import { eventPoolLaden } from "@/lib/daten";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { jsonLdText } from "@/lib/json-ld";
import { guideStadtteilPfad, inStadtteil, kanonischerStadtteil, stadtteilPfad } from "@/lib/landing";
import { naheCafesLaden, orteLaden, ortBildAutorUrl, ortBildFokus, ortBildUrl, slugDekodieren, type NaheCafe } from "@/lib/orte";
import { seitenMetadaten } from "@/lib/seo";
import {
  EXTRAS, GERAETE, NEBENGERAETE, entfernungM, entfernungText, extraWert, groesseText, nachbarn, ortIndexierbar, saisonHinweis,
  spielplatz, spielplatzTitel, typInfo, type Eintrag, type SpielplatzDaten,
} from "@/lib/spielplaetze";
import { spielplaetzeLaden, spielplatzLaden } from "@/lib/spielplaetze-daten";
import { SPIELPLATZ_BASIS as BASIS, spielplatzJsonLd, spielplatzPfad } from "@/lib/spielplaetze-json-ld";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddOrt } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
const NAEHE_ID = "sp-naehe";
type Props = { params: Promise<{ slug: string }> };

async function laden(props: Props): Promise<DddOrt | null> {
  const slug = slugDekodieren((await props.params).slug);
  return slug ? spielplatzLaden(slug) : null;
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const ort = await laden(props);
  if (!ort) return { title: "Nicht gefunden" };
  const sp = spielplatz(ort);
  const ortText = ort.stadtteil ? inStadtteil(ort.stadtteil) : "in Düsseldorf";
  return seitenMetadaten({
    pfad: spielplatzPfad(ort),
    titel: spielplatzTitel(ort),
    beschreibung: kurzBeschreibung(sp.beschreibung, 160) ?? `${typInfo(ort).label} ${ortText}: Lage, Größe, Ausstattung`,
    bild: ortBildUrl(ort) ?? undefined,
    noindex: !ortIndexierbar(ort),
  });
}

// ---------- Bausteine ----------

/** „Bereich für Kleinkinder“ usw. aus den zusammengeführten Teilflächen der Stadt. */
function bereiche(sp: SpielplatzDaten): string[] {
  const teile = sp.teile ?? [];
  if (teile.length < 2) return [];
  const art = (t: (typeof teile)[number]) => {
    const roh = t.objektart.replace(/^\d+\s*/, "");
    const fuer = /kleinkind/i.test(t.stadt_name) ? " für Kleinkinder" : /schulkind/i.test(t.stadt_name) ? " für Schulkinder" : "";
    const basis = roh === "Wasserspielplatz" ? "Wasserbereich" : roh === "Waldkinderspielplatz" ? "Waldspielbereich" : "Spielbereich";
    const groesse = t.groesse_m2 ? ` (ca. ${Math.round(t.groesse_m2).toLocaleString("de-DE")} m²)` : "";
    return `${basis}${fuer}${groesse}`;
  };
  return teile.map(art);
}

// foto_ki/luftbild_ki: KI-Erkennung auf Besucherfotos bzw. NRW-Luftbild ab Konfidenz 0,8 (Auftraggeber 25.11.2026)
const BELEG_QUELLEN = ["osm", "zitat", "sichtung", "foto_ki", "luftbild_ki"];
/** „nein“ nur mit Beleg (5.3), sonst gilt es als keine Angabe. */
function status(e: Eintrag | undefined): "ja" | "nein" | "teilweise" | null {
  if (!e) return null;
  if (e.wert === "nein") return BELEG_QUELLEN.includes(e.quelle ?? "") && e.beleg ? "nein" : null;
  return e.wert;
}

/** Hinweis bei Geräten aus der KI-Erkennung (Auftraggeber 25.11.2026) */
const KI_HINWEIS: Record<string, string> = { foto_ki: "auf Besucherfotos erkannt", luftbild_ki: "aus Luftbild" };

function Ausstattung({ sp }: { sp: SpielplatzDaten }) {
  const a = sp.ausstattung ?? {};
  const neben = NEBENGERAETE.filter((g) => status(a[g.wert]) === "ja");
  const label = { ja: "vorhanden", nein: "nicht vorhanden", teilweise: "teilweise" } as const;
  return (
    <section className="sp-block">
      <h2 className="d">Ausstattung</h2>
      <ul className="sp-ausstattung">
        {GERAETE.map((g) => {
          const s = status(a[g.wert]);
          return (
            <li key={g.wert} className={`sp-ausstattung__zeile sp-ausstattung__zeile--${s ?? "offen"}`}>
              <Icon name={s === "ja" ? "check_circle" : s === "nein" ? "cancel" : "help"} className="sp-ausstattung__status" />
              <span className="sp-ausstattung__name">{g.label}<span className="sr-only">: {s ? label[s] : "keine Angabe"}</span></span>
              {!s && <span className="sp-ausstattung__offen" aria-hidden>keine Angabe</span>}
              {s === "ja" && KI_HINWEIS[a[g.wert]?.quelle ?? ""] && (
                <span className="sp-ausstattung__offen">{KI_HINWEIS[a[g.wert]!.quelle!]}</span>
              )}
              <span title={g.label}><Icon name={g.icon} className="sp-ausstattung__icon" /></span>
            </li>
          );
        })}
      </ul>
      {neben.length > 0 && <p className="sp-neben">Außerdem: {neben.map((g) => g.label).join(", ")}</p>}
    </section>
  );
}

function Extras({ sp }: { sp: SpielplatzDaten }) {
  const text = { ja: "Ja", nein: "Nein", teilweise: "Teilweise" } as const;
  return (
    <section className="sp-block">
      <h2 className="d">Extras</h2>
      <ul className="sp-extras">
        {EXTRAS.map((x) => {
          const e = extraWert(sp, x.wert);
          const s = status(e ?? undefined);
          return (
            <li key={x.wert} className="sp-extras__zeile">
              <span className="sp-extras__kachel" title={x.label}><Icon name={x.icon} /></span>
              <span className="sp-extras__label muted">{x.label}</span>
              <span className={`sp-status sp-status--${s ?? "offen"}`}>{s ? text[s] : "keine Angabe"}</span>
              {s && e?.notiz && <span className="sp-extras__notiz muted">{e.notiz}</span>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}


function domain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

/** Cafés in der Nähe (Auftraggeber 25.11.2026): die drei nächsten im Umkreis von 2 km statt zwei im Umkreis von 1 km */
const CAFES_ANZAHL = 3;
const CAFES_UMKREIS_M = 2000;

/** „300 m“, „300 m und 1,2 km“, „300 m, 800 m und 1,2 km“ */
function aufzaehlung(teile: string[]): string {
  return teile.length < 2 ? (teile[0] ?? "") : `${teile.slice(0, -1).join(", ")} und ${teile.at(-1)}`;
}

/** Ein Café in der Nähe: Guide-Café (`o` gesetzt, Karte mit „Empfehlung“) oder Café ab Score 5 ohne Guide-Seite */
type CafeTreffer = { id: string; m: number; o: DddOrt | null; c: NaheCafe | null };

/**
 * Die drei nächsten Cafés im Umkreis von 2 km (Auftraggeber 25.11.2026): Guide-Cafés (Score ≥ 7) als Karte mit Pill
 * „Empfehlung“, Cafés mit Score 5–6 als schlichte Zeile mit Link zu Google Maps (sie haben keine eigene Seite).
 * Ohne die Ansicht cafes_naehe nur Guide-Cafés wie bisher.
 */
async function Cafes({ ort }: { ort: DddOrt }) {
  if (ort.latitude == null || ort.longitude == null) return null;
  const p = { lat: ort.latitude, lng: ort.longitude };
  const guide = (await orteLaden("cafe")).filter((o) => o.typ === "cafe" && o.latitude != null && o.longitude != null);
  const guideNachId = new Map(guide.map((o) => [o.id, o]));
  const weitere = await naheCafesLaden();
  const kandidaten: CafeTreffer[] = weitere
    ? weitere.map((c) => ({ id: c.id, m: entfernungM(p, { lat: c.latitude, lng: c.longitude }), o: guideNachId.get(c.id) ?? null, c }))
    : guide.map((o) => ({ id: o.id, m: entfernungM(p, { lat: o.latitude!, lng: o.longitude! }), o, c: null }));
  const cafes = kandidaten.filter((x) => x.m <= CAFES_UMKREIS_M).sort((a, b) => a.m - b.m).slice(0, CAFES_ANZAHL);
  if (!cafes.length) return null;
  const empfohlen = cafes.filter((x) => x.o);
  const einfach = cafes.filter((x) => !x.o && x.c);
  return (
    <section className="sp-naehe__block sp-naehe__cafes">
      <h3 className="sp-naehe__titel"><span className="sp-naehe__kreis" aria-hidden><Icon name="local_cafe" /></span>Cafés in der Nähe</h3>
      <p className="muted sp-naehe__zusatz">Perfekt für einen Kaffee danach · {aufzaehlung(cafes.map((c) => entfernungText(c.m)))} entfernt</p>
      {empfohlen.length > 0 && (
        <div className="gd-grid sp-naehe__grid" role="list">
          {empfohlen.map((x) => <OrtKarte key={x.id} o={x.o!} hinweis="Empfehlung" />)}
        </div>
      )}
      {einfach.length > 0 && (
        <ul className="sp-cafes-weitere">
          {einfach.map(({ id, m, c }) => (
            <li key={id} className="sp-cafe">
              <span className="sp-cafe__name">{c!.name}</span>
              <span className="sp-cafe__meta muted">
                {[c!.stadtteil, c!.google_rating != null ? `★ ${c!.google_rating.toLocaleString("de-DE")}` : null, entfernungText(m)].filter(Boolean).join(" · ")}
              </span>
              {c!.google_maps_url && (
                <a className="link sp-cafe__link" href={c!.google_maps_url} target="_blank" rel="noopener noreferrer nofollow">
                  In Google Maps öffnen <Icon name="open_in_new" />
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

async function FamilienEvents({ ort }: { ort: DddOrt }) {
  const st = kanonischerStadtteil(ort.stadtteil);
  if (!st) return null;
  const pool = await eventPoolLaden();
  const events = pool.events
    .filter((e) => e.kategorie === "familie" && kanonischerStadtteil(e.stadtteil) === st && (e.datum_bis ?? e.datum) >= pool.heute)
    .slice(0, 3);
  if (!events.length) return null;
  const seite = stadtteilPfad(st);
  return (
    <section className="sp-naehe__block sp-naehe__events">
      <h3 className="sp-naehe__titel"><span className="sp-naehe__kreis" aria-hidden><Icon name="family_restroom" /></span>Familien-Events {inStadtteil(st)}</h3>
      <Reihe breite={258} label={`Familien-Events ${inStadtteil(st)}`}>
        {events.map((e) => <EventKarte key={e.id} e={e} heute={pool.heute} variante="reihe" />)}
      </Reihe>
      <Link href={seite ?? "/kategorie/familie"} className="link">Mehr Events {inStadtteil(st)}</Link>
    </section>
  );
}

async function WeitereSpielplaetze({ ort }: { ort: DddOrt }) {
  const n = nachbarn(ort, await spielplaetzeLaden());
  if (!n.orte.length) return null;
  return (
    <section className="sp-naehe__block">
      <h3 className="sp-naehe__titel"><span className="sp-naehe__kreis" aria-hidden><Icon name="sp:spielplatz" /></span>{n.titel}</h3>
      <div className="gd-grid sp-naehe__grid" role="list">
        {n.orte.map(({ o, m }) => <SpielplatzKarte key={o.id} o={o} meter={m} />)}
      </div>
    </section>
  );
}

// ---------- Seite ----------

export default async function SpielplatzDetail(props: Props) {
  const ort = await laden(props);
  if (!ort) notFound();

  const sp = spielplatz(ort);
  const typ = typInfo(ort);
  const foto = ortBildUrl(ort);
  const autorUrl = ortBildAutorUrl(ort);
  const pfad = spielplatzPfad(ort);
  const st = ort.stadtteil ? stadtteilName(ort.stadtteil) : null;
  const lageZeile = [st, ort.adresse].filter(Boolean).join(" · ");
  const ziel = ort.latitude != null && ort.longitude != null ? `${ort.latitude},${ort.longitude}` : [ort.name, ort.adresse ?? "Düsseldorf"].join(", ");
  const routeUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(ziel)}`;
  const kartenAdresse = ort.latitude != null && ort.longitude != null ? `${ort.latitude},${ort.longitude}` : ziel;
  const saison = saisonHinweis(sp);
  const groesse = groesseText(sp);
  const teilBereiche = bereiche(sp);
  const quellen = (sp.profil?.quellen ?? []).filter((u) => /^https:\/\//.test(u)).slice(0, 6);
  const kanonischerSt = kanonischerStadtteil(ort.stadtteil);

  const krumen = [
    { name: "Start", pfad: "/" },
    { name: "Spielplätze", pfad: BASIS },
    { name: ort.name, pfad },
  ];
  const jsonLd = [spielplatzJsonLd(ort, SITE_URL), brotkrumenJsonLd(SITE_URL, krumen)];

  return (
    <div className="container gd-detail gd-seite sp-seite sp-detail">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link><span>/</span>
        <Link href={BASIS}>Spielplätze</Link><span>/</span>
        <span aria-current="page">{ort.name}</span>
      </nav>

      <div className="gd-detail__hero sp-detail__hero">
        <BildImg
          src={foto ?? typ.bild}
          ersatz={foto ? typ.bild : null}
          alt={foto ? `${ort.name} ${st ? inStadtteil(ort.stadtteil!) : "in Düsseldorf"}` : ""}
          icon={typ.icon}
          eager
          fokus={ortBildFokus(ort)}
        />
        {foto && ort.bild_attribution && (
          <span className="gd-detail__credit">
            Foto:{" "}
            {autorUrl ? <a href={autorUrl} target="_blank" rel="noopener noreferrer">{ort.bild_attribution}</a> : ort.bild_attribution}
          </span>
        )}
      </div>

      <div className="gd-detail__spalten sp-detail__spalten">
        <div className="gd-detail__haupt">
          <span className="gd-typ gd-typ--gross"><Icon name={typ.icon} />{typ.label}</span>
          <h1 className="d sp-detail__titel">{ort.name}</h1>
          {lageZeile && <p className="sp-detail__lage muted"><Icon name="location_on" />{lageZeile}</p>}
          <AlterBadge o={ort} gross />
          <BeschreibungText text={sp.beschreibung} />

          {teilBereiche.length > 0 && (
            <section className="sp-block">
              <h2 className="d">Bereiche</h2>
              <ul className="sp-bereiche">{teilBereiche.map((b, i) => <li key={i}>{b}</li>)}</ul>
            </section>
          )}

          <Ausstattung sp={sp} />
          <Extras sp={sp} />

          <section className="sp-block sp-fakten">
            <h2 className="d">Gut zu wissen</h2>
            {groesse && <InfoZeile icon="straighten" l1={groesse} l2="Größe" />}
            {sp.typ === "abenteuer" && ort.oeffnungszeiten && (
              <Suspense fallback={<InfoZeile icon="schedule" l1="Öffnungszeiten" />}>
                <Oeffnungszeiten text={ort.oeffnungszeiten} />
              </Suspense>
            )}
            {sp.typ === "abenteuer" && sp.traeger && <InfoZeile icon="groups" l1={sp.traeger} l2="Träger" />}
            {saison && <InfoZeile icon="water_drop" l1={saison.text} l2={saison.label} />}
          </section>

          {/* Notfallnummer und „Stand der Angaben“ entfernt (Auftraggeber 25.11.2026) */}
          <div className="sp-stand muted">
            <p>
              <b>Quellen:</b>{" "}
              {sp.quelle_url ? <a href={sp.quelle_url} target="_blank" rel="noopener noreferrer">Spielplatzdaten der Landeshauptstadt Düsseldorf</a> : sp.quelle === "abenteuer" ? "Angaben des Trägers" : "Spielplatzdaten der Landeshauptstadt Düsseldorf"}
              {quellen.map((u) => (
                <span key={u}>, <a href={u} target="_blank" rel="noopener noreferrer nofollow">{domain(u)}</a></span>
              ))}
            </p>
            {sp.osm?.id && (
              <p>Ausstattung teils aus <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap-Mitwirkende</a></p>
            )}
            {Object.values(sp.ausstattung ?? {}).some((e) => e?.quelle === "foto_ki" || e?.quelle === "luftbild_ki") && (
              <p>Einige Geräte wurden automatisch auf Besucherfotos bzw. im Luftbild (© Geobasis NRW) erkannt.</p>
            )}
            <p>Angaben ohne Gewähr. Geräte können umgebaut oder gesperrt sein.</p>
          </div>
        </div>

        <aside className="gd-detail__seite sp-detail__seite">
          <div className="sp-seitenpanel">
            <GoogleKarte adresse={kartenAdresse} routeUrl={routeUrl} />
            {ort.adresse && <p className="sp-seitenpanel__adresse"><Icon name="location_on" />{ort.adresse}</p>}
            <a href={routeUrl} target="_blank" rel="noopener noreferrer" className="gd-knopf gd-knopf--navy">
              <Icon name="directions" />Route planen
            </a>
            <a href={`#${NAEHE_ID}`} className="gd-knopf sp-knopf-naehe">
              <Icon name="near_me" />In der Nähe
            </a>
            {kanonischerSt && (
              <Link href={guideStadtteilPfad("spielplaetze", kanonischerSt)} className="link">Spielplätze {inStadtteil(kanonischerSt)}</Link>
            )}
          </div>
        </aside>
      </div>

      <section id={NAEHE_ID} className="sp-naehe" aria-labelledby={`${NAEHE_ID}-titel`}>
        <h2 className="d" id={`${NAEHE_ID}-titel`}>In der Nähe</h2>
        <Suspense fallback={null}>
          <WeitereSpielplaetze ort={ort} />
        </Suspense>
        <div className="sp-naehe__unten">
          <Suspense fallback={null}>
            <Cafes ort={ort} />
          </Suspense>
          <Suspense fallback={null}>
            <FamilienEvents ort={ort} />
          </Suspense>
        </div>
      </section>
    </div>
  );
}
