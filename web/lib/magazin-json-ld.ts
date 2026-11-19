// Strukturierte Daten des Magazins (Plan 5.4, Autorenkonzept 2.3 Punkt 6):
// author = Organisation „Redaktion dies.das.düsseldorf“, accountablePerson = die echte verantwortliche Person.
// Das Pseudonym steht nur sichtbar auf der Seite, NIE im JSON-LD (kein Person-Objekt für Pseudonyme).
import { eventPfad } from "./pfade";
import { berlinIso, beitragPfad, RUBRIK_NAME, REDAKTION_NAME, VERANTWORTLICH, type MagazinBeitrag } from "./magazin";
import { heroFuer, zuschnittUrl, ZUSCHNITTE } from "./magazin-bilder";
import type { DddEvent } from "./typen";

export const redaktionId = (siteUrl: string) => `${siteUrl}/magazin/redaktion#redaktion`;

function redaktion(siteUrl: string): Record<string, unknown> {
  return { "@type": "Organization", "@id": redaktionId(siteUrl), name: REDAKTION_NAME, url: `${siteUrl}/magazin/redaktion` };
}

function brotkrumen(siteUrl: string, teile: { name: string; pfad: string }[]): Record<string, unknown> {
  return {
    "@type": "BreadcrumbList",
    itemListElement: teile.map((t, i) => ({ "@type": "ListItem", position: i + 1, name: t.name, item: `${siteUrl}${t.pfad}` })),
  };
}

/** headline höchstens 110 Zeichen (Google kürzt sonst), an einer Wortgrenze. */
export function kurzeHeadline(titel: string): string {
  if (titel.length <= 110) return titel;
  const schnitt = titel.slice(0, 109);
  const grenze = schnitt.lastIndexOf(" ");
  return `${(grenze > 60 ? schnitt.slice(0, grenze) : schnitt).replace(/[\s,;:–-]+$/, "")}…`;
}

/** Article + BreadcrumbList (+ FAQPage) eines veröffentlichten Beitrags. */
export function artikelJsonLd(siteUrl: string, b: MagazinBeitrag, events: DddEvent[] = []): Record<string, unknown> {
  const url = `${siteUrl}${beitragPfad(b)}`;
  const hero = heroFuer(b);
  const veroeffentlicht = b.veroeffentlicht_am ? berlinIso(b.veroeffentlicht_am) : undefined;
  const geaendert = b.aktualisiert_am ? berlinIso(b.aktualisiert_am) : veroeffentlicht;
  const artikel: Record<string, unknown> = {
    "@type": "Article",
    "@id": `${url}#artikel`,
    headline: kurzeHeadline(b.titel),
    ...(b.teaser ? { description: b.teaser } : {}),
    image: ZUSCHNITTE.map((z) => `${siteUrl}${zuschnittUrl(hero.pfad, z)}`),
    ...(veroeffentlicht ? { datePublished: veroeffentlicht } : {}),
    ...(geaendert ? { dateModified: geaendert } : {}),
    author: redaktion(siteUrl),
    accountablePerson: { "@type": "Person", name: VERANTWORTLICH, url: `${siteUrl}/impressum` },
    publisher: { "@id": `${siteUrl}/#organisation` },
    mainEntityOfPage: url,
    inLanguage: "de-DE",
    isAccessibleForFree: true,
    articleSection: RUBRIK_NAME[b.rubrik],
    // Nur Verweise auf die Event-Seiten (dort steht das Event-Markup), kein eigenes Event-Markup
    ...(events.length ? { mentions: events.filter((e) => e.slug).map((e) => ({ "@id": `${siteUrl}${eventPfad(e)}` })) } : {}),
  };
  const graph: Record<string, unknown>[] = [
    artikel,
    brotkrumen(siteUrl, [
      { name: "Start", pfad: "/" },
      { name: "Magazin", pfad: "/magazin" },
      { name: RUBRIK_NAME[b.rubrik], pfad: `/magazin/rubrik/${b.rubrik}` },
      { name: b.titel, pfad: beitragPfad(b) },
    ]),
  ];
  if (b.faq?.length) {
    graph.push({
      "@type": "FAQPage",
      mainEntity: b.faq.map((f) => ({ "@type": "Question", name: f.frage, acceptedAnswer: { "@type": "Answer", text: f.antwort } })),
    });
  }
  return { "@context": "https://schema.org", "@graph": graph };
}

/**
 * Autorenseite: WebPage + BreadcrumbList, about → Redaktion. Kein ProfilePage, keine Person, und der Name des Pseudonyms
 * steht nirgends im JSON-LD (Plan 2.3 Punkt 6, Cursor-Prüfung der Umsetzung): strukturiert heißt die Seite nur
 * „Redaktionelles Pseudonym“, der Name steht allein im sichtbaren HTML.
 */
export const PSEUDONYM_SEITE = "Redaktionelles Pseudonym";

export function autorJsonLd(siteUrl: string, pfad: string): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "WebPage", "@id": `${siteUrl}${pfad}`, url: `${siteUrl}${pfad}`, name: PSEUDONYM_SEITE, inLanguage: "de-DE", about: { "@id": redaktionId(siteUrl) } },
      brotkrumen(siteUrl, [
        { name: "Start", pfad: "/" },
        { name: "Magazin", pfad: "/magazin" },
        { name: "Unsere Redaktion", pfad: "/magazin/redaktion" },
        { name: PSEUDONYM_SEITE, pfad },
      ]),
    ],
  };
}

/** „Unsere Redaktion“: AboutPage mit der Redaktion als Hauptentität (Teil der Organisation). */
export function redaktionJsonLd(siteUrl: string): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "AboutPage",
        "@id": `${siteUrl}/magazin/redaktion`,
        url: `${siteUrl}/magazin/redaktion`,
        name: "Unsere Redaktion",
        inLanguage: "de-DE",
        mainEntity: { ...redaktion(siteUrl), parentOrganization: { "@id": `${siteUrl}/#organisation` } },
      },
      brotkrumen(siteUrl, [
        { name: "Start", pfad: "/" },
        { name: "Magazin", pfad: "/magazin" },
        { name: "Unsere Redaktion", pfad: "/magazin/redaktion" },
      ]),
    ],
  };
}
