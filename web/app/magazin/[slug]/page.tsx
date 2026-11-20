// Magazin-Beitrag (Plan docs/plan-redaktion-2026-11-19.md, 5.2). Inhalt in der ersten HTML-Antwort; unbekannte,
// zurückgezogene oder noch nicht sichtbare Slugs beantwortet proxy.ts mit 404, alte Slugs mit 308.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AutorZeile, BeitragKarte, datumText, MagazinText } from "@/components/magazin";
import { Icon } from "@/components/karten";
import { jsonLdText } from "@/lib/json-ld";
import {
  beitragPfad, entstehungsHinweis, istArchiviert, istVorbei, lesezeit, RUBRIK_NAME, rubrikPfad, saisonVorbei,
} from "@/lib/magazin";
import { heroFuer, zuschnittUrl } from "@/lib/magazin-bilder";
import { autorenLaden, beitraegeLaden, beitragLaden, eventsFuerIds, magazinHeute, orteFuerSlugs } from "@/lib/magazin-daten";
import { artikelJsonLd } from "@/lib/magazin-json-ld";
import { inhaltsverzeichnis, linkZiel, parsen } from "@/lib/magazin-markdown";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";
import { seitenMetadaten } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type Props = { params: Promise<{ slug: string }> };

async function laden(props: Props) {
  const { slug } = await props.params;
  return beitragLaden(decodeURIComponent(slug));
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const b = await laden(props);
  if (!b) return { title: "Beitrag nicht gefunden" };
  const heute = await magazinHeute();
  const hero = heroFuer(b);
  return seitenMetadaten({
    pfad: beitragPfad(b),
    titel: b.seo_titel ?? b.titel,
    beschreibung: b.teaser ?? undefined,
    // 16:9-Zuschnitt, 1200×675 (Discover, Plan 5.5)
    bild: zuschnittUrl(hero.pfad, "16x9"),
    bildAlt: hero.alt,
    // Schalter aus (T9) oder archivierte Ausgabe (E12): noindex,follow
    noindex: !MAGAZIN_VERLINKT || istArchiviert(b, heute),
    artikel: b.veroeffentlicht_am ? { veroeffentlicht: b.veroeffentlicht_am, aktualisiert: b.aktualisiert_am, rubrik: RUBRIK_NAME[b.rubrik] } : undefined,
  });
}

export default function BeitragSeite(props: Props) {
  return <BeitragInhalt params={props.params} />;
}

async function BeitragInhalt({ params }: Props) {
  const b = await laden({ params });
  if (!b) notFound();
  const [heute, autoren, alle, { events }, orte] = await Promise.all([
    magazinHeute(), autorenLaden(), beitraegeLaden(), eventsFuerIds(b.event_ids), orteFuerSlugs(b.ort_slugs),
  ]);
  const autor = autoren.find((a) => a.slug === b.autor_slug) ?? null;
  const hero = heroFuer(b);
  const bloecke = parsen(b.inhalt_md);
  const toc = inhaltsverzeichnis(bloecke);
  const aktuell = alle.find((x) => x.rubrik === b.rubrik && x.id !== b.id && (x.gueltig_von ?? "") > (b.gueltig_von ?? ""));
  const weiter = [...alle.filter((x) => x.id !== b.id && x.rubrik === b.rubrik), ...alle.filter((x) => x.id !== b.id && x.rubrik !== b.rubrik)].slice(0, 3);

  return (
    <article className="container sektion mz-beitrag">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(artikelJsonLd(SITE_URL, b, events)) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <Link href="/magazin">Magazin</Link>
        <span>/</span>
        <Link href={rubrikPfad(b.rubrik)}>{RUBRIK_NAME[b.rubrik]}</Link>
      </nav>

      {istVorbei(b, heute) && (
        <p className="mz-hinweis" role="status">
          <Icon name="info" /> Diese Vorschau ist vorbei.{" "}
          {aktuell ? <Link href={beitragPfad(aktuell)}>Zur aktuellen Ausgabe</Link> : <Link href={rubrikPfad(b.rubrik)}>Alle Ausgaben</Link>}
        </p>
      )}
      {saisonVorbei(b, heute) && (
        <p className="mz-hinweis" role="status">
          <Icon name="info" /> Diese Saison ist vorbei – die Termine fürs nächste Jahr ergänzen wir rechtzeitig.
        </p>
      )}

      <header className="mz-kopf">
        <span className="mz-rubrik-label">{RUBRIK_NAME[b.rubrik]}</span>
        <h1 className="d">{b.titel}</h1>
        {b.teaser && <p className="mz-teaser">{b.teaser}</p>}
        <p className="mz-zeile">
          <AutorZeile autor={autor} />
          <span className="mz-zeile__daten">
            {b.veroeffentlicht_am && <span>Veröffentlicht am {datumText(b.veroeffentlicht_am)}</span>}
            {b.aktualisiert_am && <span> · Aktualisiert am {datumText(b.aktualisiert_am)}</span>}
            <span> · {lesezeit(b.inhalt_md)} Min. Lesezeit</span>
          </span>
        </p>
      </header>

      <figure className="mz-hero">
        {/* eslint-disable-next-line @next/next/no-img-element -- statische, bereits optimierte Datei aus public/ */}
        <img src={hero.pfad} alt={hero.alt} width={1200} height={675} fetchPriority="high" decoding="async" />
        {/* Nachweis nur bei fremden Bildern, KI-Symbolbilder immer gekennzeichnet (Auftraggeber, 20.11.2026) */}
        {(hero.ki || hero.nachweis) && (
          <figcaption>
            {hero.ki ? "Symbolbild (KI-generiert)" : hero.nachweis}
            {hero.ki && hero.nachweis && hero.nachweis !== "Symbolbild" ? ` · ${hero.nachweis}` : ""}
          </figcaption>
        )}
      </figure>

      {b.kurzfassung?.length ? (
        <aside className="mz-blick" aria-labelledby="mz-blick">
          <h2 id="mz-blick" className="mz-blick__titel">Auf einen Blick</h2>
          <ul>{b.kurzfassung.map((k, i) => <li key={i}>{k}</li>)}</ul>
        </aside>
      ) : null}

      {toc.length > 0 && (
        <details className="mz-toc" open>
          <summary>Inhalt</summary>
          <ol>{toc.map((t) => <li key={t.id}><a href={`#${t.id}`}>{t.text}</a></li>)}</ol>
        </details>
      )}

      <MagazinText bloecke={bloecke} events={events} orte={orte} heute={heute} />

      {b.faq?.length ? (
        <section className="mz-faq" aria-labelledby="mz-faq">
          <h2 id="mz-faq" className="d">Häufige Fragen</h2>
          {b.faq.map((f, i) => (
            <details key={i}>
              <summary>{f.frage}</summary>
              <p>{f.antwort}</p>
            </details>
          ))}
        </section>
      ) : null}

      {b.quellen.length > 0 && (
        <section className="mz-quellen" aria-labelledby="mz-quellen">
          <h2 id="mz-quellen">Quellen</h2>
          <ul>
            {b.quellen.map((q, i) => {
              // Dieselbe Prüfung wie im Text (linkZiel); nur https:// wird ein Link, alles andere bleibt Text
              const ziel = linkZiel(q.url);
              return (
                <li key={i}>
                  {ziel?.extern ? <a href={ziel.href} rel="noopener nofollow" target="_blank">{q.titel}</a> : q.titel}
                  {q.abgerufen_am ? ` (abgerufen am ${q.abgerufen_am})` : ""}
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {b.korrektur_hinweis && (
        <p className="mz-korrektur">
          <strong>Korrektur:</strong> {b.korrektur_hinweis}
        </p>
      )}

      <p className="mz-entstehung">
        {entstehungsHinweis(b)}
      </p>

      {weiter.length > 0 && (
        <section className="sektion" aria-labelledby="mz-weiter">
          <h2 id="mz-weiter" className="d">Weiterlesen</h2>
          <div className="mz-liste" role="list">
            {weiter.map((x) => <BeitragKarte key={x.id} b={x} />)}
          </div>
        </section>
      )}
    </article>
  );
}
