// Gemeinsamer Kern eines Magazin-Beitrags (Plan Admin-Dashboard 4.6, Cursor-Prüfung 3, Befund 3): Kopf mit Autor,
// Aufmacher, „Auf einen Blick“, Text mit Einbettungen, Entstehungshinweis. Genutzt von der Entwurfs-Vorschau
// (/magazin/vorschau/[id]) und der Admin-Vorschau. Die öffentliche Beitragsseite bleibt unverändert (eigene Blöcke:
// Lesezeit, Inhaltsverzeichnis, FAQ, Quellen, Korrekturhinweis, Weiterlesen).
import { AutorZeile, MagazinText } from "@/components/magazin";
import { RUBRIK_NAME, entstehungsHinweis, type MagazinAutor, type MagazinBeitrag } from "@/lib/magazin";
import { heroFuer } from "@/lib/magazin-bilder";
import { parsen } from "@/lib/magazin-markdown";
import type { ComponentProps } from "react";
import type { DddEvent } from "@/lib/typen";

type Orte = ComponentProps<typeof MagazinText>["orte"];

export function MagazinArtikel({
  b,
  autor,
  events,
  orte,
  heute,
  ersatzHinweis = false,
}: {
  b: MagazinBeitrag;
  autor: MagazinAutor | null;
  events: DddEvent[];
  orte: Orte;
  heute: string;
  /** Hinweis „Rubrik-Ersatzbild“ in der Bildunterschrift (nur Vorschauen) */
  ersatzHinweis?: boolean;
}) {
  const hero = heroFuer(b);
  return (
    <>
      <header className="mz-kopf">
        <span className="mz-rubrik-label">{RUBRIK_NAME[b.rubrik]}</span>
        <h1 className="d">{b.titel}</h1>
        {b.teaser && <p className="mz-teaser">{b.teaser}</p>}
        <p className="mz-zeile">
          <AutorZeile autor={autor} />
        </p>
      </header>
      <figure className="mz-hero">
        {/* eslint-disable-next-line @next/next/no-img-element -- statische Datei aus public/ */}
        <img src={hero.pfad} alt={hero.alt} width={1200} height={675} />
        {(hero.ki || hero.nachweis || (ersatzHinweis && hero.ersatz)) && (
          <figcaption>
            {hero.ki ? "Symbolbild (KI-generiert)" : hero.nachweis}
            {ersatzHinweis && hero.ersatz ? " · Rubrik-Ersatzbild (gespeichertes Bild fehlt oder ist nicht erlaubt)" : ""}
          </figcaption>
        )}
      </figure>
      {b.kurzfassung?.length ? (
        <aside className="mz-blick">
          <h2 className="mz-blick__titel">Auf einen Blick</h2>
          <ul>
            {b.kurzfassung.map((k, i) => (
              <li key={i}>{k}</li>
            ))}
          </ul>
        </aside>
      ) : null}
      <MagazinText bloecke={parsen(b.inhalt_md)} events={events} orte={orte} heute={heute} />
      <p className="mz-entstehung">{entstehungsHinweis(b)}</p>
    </>
  );
}
