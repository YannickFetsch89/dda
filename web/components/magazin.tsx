// Darstellung des Magazins (Plan docs/plan-redaktion-2026-11-19.md, 5.2): Text mit Einbettungen, schmale Ort-Karte
// (ohne Google-Foto und -Bewertung), Guide- und Tag-Kasten, Beitragskarten, Autorenzeile. Alles Server-Komponenten.
import Link from "next/link";
import { EventKarte, Icon } from "./karten";
import { typIcon, typLabel } from "./ort-karten";
import { tagLang } from "@/lib/datum";
import {
  autorPfad, beitragPfad, berlinTag, GUIDE_KAESTEN, RUBRIK_NAME, rubrikPfad, type MagazinAutor, type MagazinBeitrag,
} from "@/lib/magazin";
import { heroFuer } from "@/lib/magazin-bilder";
import type { MagazinOrt } from "@/lib/magazin-daten";
import type { Block, Inline } from "@/lib/magazin-markdown";
import { SPIELPLAETZE_VERLINKT } from "@/lib/schalter";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddEvent } from "@/lib/typen";

function InlineText({ teile }: { teile: Inline[] }) {
  return (
    <>
      {teile.map((t, i) => {
        if (t.art === "text") return <span key={i}>{t.text}</span>;
        if (t.art === "fett") return <strong key={i}><InlineText teile={t.kinder} /></strong>;
        // mailto nur auf Adressen von diesdas.events (linkZiel) – normales <a>, kein next/link
        if (t.href.startsWith("mailto:")) return <a key={i} href={t.href}><InlineText teile={t.kinder} /></a>;
        return t.extern ? (
          <a key={i} href={t.href} rel="noopener" target="_blank">
            <InlineText teile={t.kinder} />
          </a>
        ) : (
          <Link key={i} href={t.href}>
            <InlineText teile={t.kinder} />
          </Link>
        );
      })}
    </>
  );
}

/** Schmale Ort-Karte (Plan 5.2 Punkt 7, Cursor-Prüfung 1 Befund 7): Name, Typ, Stadtteil, Link. Kein Bild, keine Bewertung. */
export function MagazinOrtKarte({ ort }: { ort: MagazinOrt }) {
  const inhalt = (
    <>
      <span className="mz-ort__icon"><Icon name={typIcon(ort.typ)} /></span>
      <span className="mz-ort__text">
        <span className="mz-ort__name">{ort.name}</span>
        <span className="mz-ort__sub">
          {typLabel(ort.typ)}
          {ort.stadtteil ? ` · ${stadtteilName(ort.stadtteil)}` : ""}
        </span>
      </span>
      {ort.pfad && <span className="mz-ort__pfeil" aria-hidden>→</span>}
    </>
  );
  return ort.pfad ? (
    <Link href={ort.pfad} className="mz-ort">{inhalt}</Link>
  ) : (
    <div className="mz-ort">{inhalt}</div>
  );
}

function GuideKasten({ slug }: { slug: string }) {
  const g = GUIDE_KAESTEN[slug];
  if (!g || (slug === "spielplaetze" && !SPIELPLAETZE_VERLINKT)) return null;
  return (
    <Link href={`/guides/${slug}`} className="mz-kasten">
      <Icon name="explore" />
      <span>
        <strong>Guide: {g.label}</strong>
        <span>{g.text}</span>
      </span>
    </Link>
  );
}

function TagKasten({ tag }: { tag: string }) {
  return (
    <Link href={`/tag/${tag}`} className="mz-kasten">
      <Icon name="calendar_month" />
      <span>
        <strong>Alles am {tagLang(tag)}</strong>
        <span>Alle Events dieses Tages in Düsseldorf</span>
      </span>
    </Link>
  );
}

/** Beitragstext mit Einbettungen. Events und Orte kommen live aus der Datenbank (Plan T3). */
export function MagazinText({ bloecke, events, orte, heute }: { bloecke: Block[]; events: DddEvent[]; orte: MagazinOrt[]; heute: string }) {
  const eventNach = new Map(events.map((e) => [e.id, e]));
  const ortNach = new Map(orte.map((o) => [o.slug, o]));
  return (
    <div className="mz-text">
      {bloecke.map((b, i) => {
        switch (b.art) {
          case "h2":
            return <h2 key={i} id={b.id} className="d">{b.text}</h2>;
          case "h3":
            return <h3 key={i}>{b.text}</h3>;
          case "absatz":
            return <p key={i}><InlineText teile={b.inhalt} /></p>;
          case "liste": {
            const punkte = b.punkte.map((p, j) => <li key={j}><InlineText teile={p} /></li>);
            return b.nummeriert ? <ol key={i}>{punkte}</ol> : <ul key={i}>{punkte}</ul>;
          }
          case "einbettung": {
            if (b.typ === "event") {
              const e = eventNach.get(b.id);
              return e ? (
                <div key={i} className="mz-einbettung" role="list">
                  <EventKarte e={e} heute={heute} />
                </div>
              ) : null;
            }
            if (b.typ === "ort") {
              const o = ortNach.get(b.id);
              return o ? <MagazinOrtKarte key={i} ort={o} /> : null;
            }
            if (b.typ === "guide") return <GuideKasten key={i} slug={b.id} />;
            return <TagKasten key={i} tag={b.id} />;
          }
        }
      })}
    </div>
  );
}

/** „Veröffentlicht am …“ als lesbares Datum. */
export function datumText(zeitpunkt: string | null): string | null {
  return zeitpunkt ? tagLang(berlinTag(zeitpunkt)) : null;
}

/** Karte eines Beitrags in Listen (Übersicht, Rubrik, Autor, Weiterlesen). */
export function BeitragKarte({ b, gross = false }: { b: MagazinBeitrag; gross?: boolean }) {
  const hero = heroFuer(b);
  return (
    <article className={gross ? "mz-karte mz-karte--gross" : "mz-karte"} role="listitem">
      <div className="mz-karte__bild">
        {/* eslint-disable-next-line @next/next/no-img-element -- statische, bereits optimierte Dateien aus public/ */}
        <img src={hero.pfad} alt="" width={1200} height={675} loading={gross ? "eager" : "lazy"} decoding="async" />
      </div>
      <div className="mz-karte__text">
        <span className="mz-karte__meta">
          {RUBRIK_NAME[b.rubrik]}
          {b.veroeffentlicht_am ? ` · ${datumText(b.veroeffentlicht_am)}` : ""}
        </span>
        <h3 className={gross ? "d mz-karte__titel" : "mz-karte__titel"}>
          <Link href={beitragPfad(b)}>{b.titel}</Link>
        </h3>
        {b.teaser && <p className="mz-karte__teaser">{b.teaser}</p>}
      </div>
    </article>
  );
}

/**
 * Autorenzeile im Beitrag: „von [Autorenname]“ mit Link aufs Autorenprofil. Seit 20.11.2026 (Auftraggeber) ohne den
 * Zusatz „(redaktionelles Pseudonym)“ und ohne Link auf die Redaktionsseite – beides steht im Autorenprofil.
 */
export function AutorZeile({ autor }: { autor: MagazinAutor | null }) {
  return (
    <span className="mz-autor">
      {autor?.bild && (
        // eslint-disable-next-line @next/next/no-img-element -- kleines statisches Profilbild
        <img src={autor.bild} alt="" width={40} height={40} className="mz-autor__bild" />
      )}
      <span>
        {autor ? (
          <>
            von <Link href={autorPfad(autor)}>{autor.name}</Link>
          </>
        ) : (
          "von der Redaktion dies.das.düsseldorf"
        )}
      </span>
    </span>
  );
}

/** Rubrik-Navigation unter der Überschrift der Übersicht. */
export function RubrikLinks({ aktiv }: { aktiv?: string }) {
  return (
    <nav className="mz-rubriken" aria-label="Rubriken">
      {(Object.keys(RUBRIK_NAME) as (keyof typeof RUBRIK_NAME)[]).map((r) => (
        <Link key={r} href={rubrikPfad(r)} className={r === aktiv ? "mz-rubrik mz-rubrik--aktiv" : "mz-rubrik"} aria-current={r === aktiv ? "page" : undefined}>
          {RUBRIK_NAME[r]}
        </Link>
      ))}
    </nav>
  );
}
