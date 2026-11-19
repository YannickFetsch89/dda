// RSS 2.0 des Magazins (Plan 5.6): Namensräume atom, dc, media; alles XML-escaped; 20 neueste, nicht archivierte Beiträge.
import { beitragPfad, FEED_PFAD, FEED_TITEL, istArchiviert, type MagazinAutor, type MagazinBeitrag } from "./magazin";
import { heroFuer, zuschnittUrl } from "./magazin-bilder";

/** XML-Text maskieren (& < > " '). */
export function xml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}

/** RFC-822-Datum (pubDate), immer in GMT. */
export function rfc822(zeitpunkt: string): string {
  return new Date(zeitpunkt).toUTCString().replace("UTC", "GMT");
}

export const FEED_MAX = 20;

export function feedXml(siteUrl: string, beitraege: MagazinBeitrag[], autoren: MagazinAutor[], heute: string): string {
  const namen = new Map(autoren.map((a) => [a.slug, a.name]));
  const items = beitraege
    .filter((b) => b.veroeffentlicht_am && !istArchiviert(b, heute))
    .slice(0, FEED_MAX)
    .map((b) => {
      const url = `${siteUrl}${beitragPfad(b)}`;
      const bild = `${siteUrl}${zuschnittUrl(heroFuer(b).pfad, "16x9")}`;
      return [
        "    <item>",
        `      <title>${xml(b.titel)}</title>`,
        `      <link>${xml(url)}</link>`,
        `      <guid isPermaLink="true">${xml(url)}</guid>`,
        `      <pubDate>${rfc822(b.veroeffentlicht_am!)}</pubDate>`,
        ...(b.teaser ? [`      <description>${xml(b.teaser)}</description>`] : []),
        `      <dc:creator>${xml(namen.get(b.autor_slug) ?? "Redaktion dies.das.düsseldorf")}</dc:creator>`,
        `      <media:content url="${xml(bild)}" medium="image" type="image/webp" width="1200" height="675"/>`,
        "    </item>",
      ].join("\n");
    });
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/">',
    "  <channel>",
    `    <title>${xml(FEED_TITEL)}</title>`,
    `    <link>${xml(`${siteUrl}/magazin`)}</link>`,
    `    <description>${xml("Wochenvorschau, Monats-Tipps, Saison und Stadtleben in Düsseldorf – von der Redaktion geprüft.")}</description>`,
    "    <language>de-DE</language>",
    `    <atom:link href="${xml(`${siteUrl}${FEED_PFAD}`)}" rel="self" type="application/rss+xml"/>`,
    ...items,
    "  </channel>",
    "</rss>",
    "",
  ].join("\n");
}
