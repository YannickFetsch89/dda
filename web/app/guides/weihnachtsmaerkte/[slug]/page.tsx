// Guide-Detail Weihnachtsmarkt (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, 5.3; Stufe 1a)
// Name, Zeitentabelle, Sonderzeiten, Merkmale und Anfahrt stehen in der ersten HTML-Antwort. „Heute geöffnet“ rechnet
// nur der Browser (Plan E5). Indexierbar nur mit Zeitraum, Wochenzeiten und Beschreibung (5.4), sonst noindex ohne Canonical.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { BeschreibungText } from "@/components/beschreibung-text";
import { BildImg, GoogleKarte } from "@/components/client";
import { Icon } from "@/components/karten";
import { InfoZeile } from "@/components/ort-detail";
import { ortPfad } from "@/components/ort-karten";
import { kneipenLaden } from "@/lib/kneipen-daten";
import { entfernungM, entfernungText } from "@/lib/spielplaetze";
import { BadgeListe, WM_BILD, WmKarte, wmIcon } from "@/components/wm-karte";
import { WmZustand } from "@/components/wm-zustand";
import { kurzBeschreibung } from "@/lib/beschreibung";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { jsonLdText } from "@/lib/json-ld";
import { inStadtteil } from "@/lib/landing";
import { orteLaden, ortBildAutorUrl, ortBildFokus, ortBildUrl, slugDekodieren } from "@/lib/orte";
import { seitenMetadaten } from "@/lib/seo";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddOrt } from "@/lib/typen";
import {
  WM_BASIS as BASIS, aktuelleSaison, badges, datumKurz, datumLang, istIndexierbar, rolleText, saisonsKompakt, sonderZeilen,
  wm, wmPfad, wochenZeilen,
} from "@/lib/weihnachtsmaerkte";
import { saisonTag, weihnachtsmaerkteLaden, weihnachtsmarktLaden } from "@/lib/weihnachtsmaerkte-daten";
import { weihnachtsmarktJsonLd } from "@/lib/weihnachtsmaerkte-json-ld";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type Props = { params: Promise<{ slug: string }> };

const MERKMAL_TEXT: Record<string, { label: string; icon: string }> = {
  eisbahn: { label: "Eisbahn", icon: "ice_skating" },
  riesenrad: { label: "Riesenrad", icon: "attractions" },
  karussell: { label: "Kinderkarussell", icon: "toys" },
  kindereisenbahn: { label: "Kindereisenbahn", icon: "train" },
  kinderprogramm: { label: "Kinderprogramm", icon: "child_care" },
  puppenbuehne: { label: "Puppen- oder Kasperletheater", icon: "theater_comedy" },
  buehnenprogramm: { label: "Bühnenprogramm", icon: "music_note" },
  kunsthandwerk: { label: "Kunsthandwerk", icon: "palette" },
  krippe: { label: "Krippe", icon: "star" },
  tassenpfand: { label: "Glühweintasse mit Pfand", icon: "local_cafe" },
  barrierefrei: { label: "Barrierefrei", icon: "accessible" },
  wc: { label: "Toiletten", icon: "wc" },
  ueberdacht: { label: "Überdacht", icon: "roofing" },
};

async function laden(props: Props): Promise<DddOrt | null> {
  const slug = slugDekodieren((await props.params).slug);
  return slug ? weihnachtsmarktLaden(slug) : null;
}

function domain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const ort = await laden(props);
  if (!ort) return { title: "Nicht gefunden" };
  const s = aktuelleSaison(wm(ort).saisons);
  const heute = await saisonTag();
  const jahr = s && heute <= s.bis ? ` ${s.jahr}` : "";
  const zeitraum = s ? `${datumLang(s.von)} bis ${datumLang(s.bis)}` : null;
  const b = badges(ort, [ort]).slice(0, 2).map((x) => x.label);
  return seitenMetadaten({
    pfad: wmPfad(ort),
    titel: `${ort.name}${jahr}: Öffnungszeiten, Anfahrt & Infos`,
    beschreibung:
      kurzBeschreibung([zeitraum ? `${ort.name} ${ort.stadtteil ? inStadtteil(ort.stadtteil) : ""}: ${zeitraum}.` : null, b.length ? `${b.join(", ")}.` : null, ort.beschreibung].filter(Boolean).join(" "), 160)
      ?? `${ort.name}: Öffnungszeiten, Sonderzeiten und Anfahrt`,
    bild: ortBildUrl(ort) ?? WM_BILD,
    bildAlt: `${ort.name}${ort.stadtteil ? ` ${inStadtteil(ort.stadtteil)}` : ""}`,
    noindex: !istIndexierbar(ort),
  });
}

function Zeitentabelle({ ort, gruppe }: { ort: DddOrt; gruppe: DddOrt | null }) {
  const s = aktuelleSaison(wm(ort).saisons);
  if (!s) {
    return (
      <section className="sp-block wm-zeiten">
        <h2 className="d">Öffnungszeiten</h2>
        <p>Öffnungszeiten noch nicht veröffentlicht.</p>
      </section>
    );
  }
  const woche = wochenZeilen(s);
  const sonder = sonderZeilen(s);
  return (
    <section className="sp-block wm-zeiten" aria-labelledby="wm-zeiten-titel">
      <h2 className="d" id="wm-zeiten-titel">Öffnungszeiten {s.jahr}</h2>
      <p className="wm-zeiten__zeitraum"><Icon name="date_range" />{datumKurz(s.von)}{s.von.slice(0, 4)} bis {datumKurz(s.bis)}{s.bis.slice(0, 4)}</p>
      <table className="wm-zeiten__tabelle">
        <caption className="sr-only">Wochenzeiten</caption>
        <tbody>
          {woche.map((z) => (
            <tr key={z.tage}><th scope="row">{z.tage}</th><td>{z.zeit}</td></tr>
          ))}
        </tbody>
      </table>
      {sonder.length > 0 && (
        <>
          <h3 className="wm-zeiten__unter">Sonderzeiten</h3>
          <table className="wm-zeiten__tabelle">
            <caption className="sr-only">Sonderzeiten</caption>
            <tbody>
              {sonder.map((z) => (
                <tr key={z.datum}><th scope="row">{datumKurz(z.datum)}{z.name ? ` (${z.name})` : ""}</th><td>{z.text}</td></tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      <p className="muted wm-zeiten__hinweis">
        An Feiertagen ohne eigene Angabe (z. B. Totensonntag) hat der Veranstalter keine Zeit veröffentlicht – dann steht oben „nicht veröffentlicht“.
        {s.geerbt?.length && gruppe ? <> Gleiche Zeiten wie der <Link href={wmPfad(gruppe)}>{gruppe.name}</Link>.</> : null}
      </p>
    </section>
  );
}

function Merkmale({ ort }: { ort: DddOrt }) {
  const m = Object.entries(wm(ort).merkmale).filter(([k, v]) => MERKMAL_TEXT[k] && (v.wert === "ja" || v.wert === "teilweise" || (v.wert === "nein" && v.beleg)));
  if (!m.length) return null;
  return (
    <section className="sp-block">
      <h2 className="d">Was es dort gibt</h2>
      <ul className="wm-merkmale">
        {m.map(([k, v]) => (
          <li key={k} className={`wm-merkmal wm-merkmal--${v.wert}`}>
            <Icon name={MERKMAL_TEXT[k].icon} />
            <span>{MERKMAL_TEXT[k].label}{v.wert === "nein" ? ": nein" : v.wert === "teilweise" ? ": teilweise" : ""}{v.notiz && v.notiz !== MERKMAL_TEXT[k].label ? <span className="muted"> · {v.notiz}</span> : null}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/**
 * „In der Nähe“ (Plan 5.3, Stufe 1b): bis zu 2 Cafés und 2 Kneipen ≤ 800 m aus den bestehenden Guides – bewusst als
 * reine Textliste ohne Google-Fotos und -Bewertungen (Google-EWR-Bedingungen, Schritt 7a).
 */
async function InDerNaehe({ ort }: { ort: DddOrt }) {
  if (ort.latitude == null || ort.longitude == null) return null;
  const p = { lat: ort.latitude, lng: ort.longitude };
  const [cafes, kneipen] = await Promise.all([orteLaden("cafe"), kneipenLaden()]);
  const naechste = (liste: DddOrt[], typ: string) =>
    liste
      .filter((o) => o.typ === typ && o.latitude != null && o.longitude != null)
      .map((o) => ({ o, m: entfernungM(p, { lat: o.latitude!, lng: o.longitude! }) }))
      .filter((x) => x.m <= 800)
      .sort((a, b) => a.m - b.m)
      .slice(0, 2);
  const treffer = [...naechste(cafes, "cafe").map((x) => ({ ...x, art: "Café" })), ...naechste(kneipen, "kneipe").map((x) => ({ ...x, art: "Kneipe oder Bar" }))];
  if (!treffer.length) return null;
  return (
    <section className="sp-block wm-naehe" aria-labelledby="wm-naehe-titel">
      <h2 className="d" id="wm-naehe-titel">Zum Aufwärmen in der Nähe</h2>
      <ul className="wm-startbox__liste wm-naehe__liste">
        {treffer.map(({ o, m, art }) => (
          <li key={o.id}>
            {/* Ganze Kachel klickbar (Auftraggeber 18.11.2026) */}
            <Link href={ortPfad(o)} className="wm-kurz__karte">
              <span className="wm-kurz__titel">{o.name}</span>
              <span className="muted">{art} · {entfernungText(m)} entfernt</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default async function WeihnachtsmarktDetail(props: Props) {
  const ort = await laden(props);
  if (!ort) notFound();
  const alle = await weihnachtsmaerkteLaden();
  const heute = await saisonTag();
  const d = wm(ort);
  const gruppe = d.gruppe ? alle.find((o) => wm(o).schluessel === d.gruppe && wm(o).ist_gruppe) ?? null : null;
  const teile = d.ist_gruppe ? alle.filter((o) => wm(o).gruppe === d.schluessel && !wm(o).ist_gruppe) : [];
  const geschwister = gruppe ? alle.filter((o) => wm(o).gruppe === d.gruppe && o.id !== ort.id && !wm(o).ist_gruppe) : [];
  const foto = ortBildUrl(ort);
  const autorUrl = ortBildAutorUrl(ort);
  const st = ort.stadtteil ? stadtteilName(ort.stadtteil) : null;
  const ziel = ort.latitude != null && ort.longitude != null ? `${ort.latitude},${ort.longitude}` : [ort.name, ort.adresse ?? "Düsseldorf"].join(", ");
  const routeUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(ziel)}`;
  const anfahrt = d.anfahrt ?? (gruppe ? wm(gruppe).anfahrt : null);
  const krumen = [
    { name: "Start", pfad: "/" },
    { name: "Weihnachtsmärkte", pfad: BASIS },
    ...(gruppe ? [{ name: gruppe.name, pfad: wmPfad(gruppe) }] : []),
    { name: ort.name, pfad: wmPfad(ort) },
  ];
  const jsonLd = [weihnachtsmarktJsonLd(ort, SITE_URL, heute), brotkrumenJsonLd(SITE_URL, krumen)];

  return (
    <div className="container gd-detail gd-seite sp-seite sp-detail wm-detail">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        {krumen.map((k, i) => (
          <span key={k.pfad}>
            {i > 0 && <span>/</span>}
            {i < krumen.length - 1 ? <Link href={k.pfad}>{k.name}</Link> : <span aria-current="page">{k.name}</span>}
          </span>
        ))}
      </nav>

      <div className="gd-detail__hero sp-detail__hero">
        <BildImg src={foto ?? WM_BILD} ersatz={foto ? WM_BILD : null} alt={foto ? `${ort.name} ${ort.stadtteil ? inStadtteil(ort.stadtteil) : ""}` : ""} icon={wmIcon(ort)} eager fokus={ortBildFokus(ort)} />
        {foto && ort.bild_attribution && (
          <span className="gd-detail__credit">
            Foto:{" "}
            {autorUrl ? <a href={autorUrl} target="_blank" rel="noopener noreferrer">{ort.bild_attribution}</a> : ort.bild_attribution}
          </span>
        )}
      </div>

      <div className="gd-detail__spalten sp-detail__spalten">
        <div className="gd-detail__haupt">
          <span className="gd-typ gd-typ--gross"><Icon name={wmIcon(ort)} />{rolleText(ort)}</span>
          <h1 className="d sp-detail__titel">{ort.name}</h1>
          {(st || ort.adresse) && <p className="sp-detail__lage muted"><Icon name="location_on" />{[st, ort.adresse].filter(Boolean).join(" · ")}</p>}
          <p className="wm-detail__zustand"><WmZustand saisons={saisonsKompakt(d.saisons)} mitUhrzeit /></p>
          <BadgeListe liste={badges(ort, alle)} max={8} />
          <BeschreibungText text={ort.beschreibung} fett />

          <Zeitentabelle ort={ort} gruppe={gruppe} />
          <Merkmale ort={ort} />

          <section className="sp-block sp-fakten">
            <h2 className="d">Gut zu wissen</h2>
            {d.eintritt && <InfoZeile icon="confirmation_number" l1={d.eintritt.wert === "frei" ? "Eintritt frei" : "Eintritt kostenpflichtig"} l2={d.eintritt.wert === "kostenpflichtig" ? d.eintritt.beleg : undefined} />}
            {anfahrt && anfahrt.haltestellen.length > 0 && (
              <InfoZeile icon="directions_transit" l1={`Haltestelle ${anfahrt.haltestellen.map((h) => h.name).join(" oder ")}`} l2="Anfahrt mit Bus und Bahn" />
            )}
            {d.veranstalter && <InfoZeile icon="groups" l1={d.veranstalter} l2="Veranstalter" />}
            {ort.webseite && <InfoZeile icon="language" l1={<a href={ort.webseite} target="_blank" rel="noopener noreferrer">{domain(ort.webseite)}</a>} l2="Website" />}
          </section>

          {teile.length > 0 && (
            <section className="sp-block">
              <h2 className="d">Märkte und Attraktionen</h2>
              <div className="gd-grid gd-grid--3" role="list">{teile.map((t) => <WmKarte key={t.id} o={t} alle={alle} tag={null} klein />)}</div>
            </section>
          )}
          {geschwister.length > 0 && (
            <section className="sp-block">
              <h2 className="d">Weitere Märkte in der Innenstadt</h2>
              <div className="gd-grid gd-grid--3" role="list">{geschwister.map((t) => <WmKarte key={t.id} o={t} alle={alle} tag={null} klein />)}</div>
            </section>
          )}

          <Suspense fallback={null}>
            <InDerNaehe ort={ort} />
          </Suspense>

          <div className="sp-stand muted">
            <p>Angaben ohne Gewähr. Die Veranstalter können Zeiten kurzfristig ändern, etwa bei Sturm – im Zweifel vorher auf der Seite des Veranstalters nachsehen.</p>
          </div>
        </div>

        <aside className="gd-detail__seite sp-detail__seite">
          <div className="sp-seitenpanel">
            <GoogleKarte adresse={ziel} routeUrl={routeUrl} />
            {ort.adresse && <p className="sp-seitenpanel__adresse"><Icon name="location_on" />{ort.adresse}</p>}
            <a href={routeUrl} target="_blank" rel="noopener noreferrer" className="gd-knopf gd-knopf--navy">
              <Icon name="directions" />Route planen
            </a>
            <Link href={BASIS} className="btn btn--gold wm-alle-knopf"><Icon name="wm:markt" />Alle Weihnachtsmärkte</Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
