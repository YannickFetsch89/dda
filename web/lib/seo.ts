// Einheitliche Seiten-Metadaten (SEO-/GEO-Plan Nov. 2026, Maßnahme 2): Canonical, Open Graph und Twitter
// aus einer Hand. metadataBase steht im Layout – Pfade bleiben relativ.
//
// Regel: Eine indexierbare Seite kanonisiert auf sich selbst. Varianten mit Filter-/Such-Parametern bekommen
// „noindex, follow“ und KEIN Canonical auf eine andere URL – beides zusammen wären widersprüchliche Signale.
import type { Metadata } from "next";

export const SITE_NAME = "dies.das.düsseldorf";
/** Erster Satz von /ueber – derselbe Satz steht in Organization.description (SEO-/GEO-Plan, Maßnahme 8). */
export const MARKE_SATZ =
  "dies.das.düsseldorf ist ein tagesaktueller Eventkalender und Freizeitguide für Düsseldorf, mit Guides auch für Neuss und Ratingen.";

/** Organization + WebSite fürs Layout: eine Entität für die Domain diesdas.events und die Schreibweise dies.das.düsseldorf. */
export function markeJsonLd(siteUrl: string): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": `${siteUrl}/#organisation`,
        name: SITE_NAME,
        url: `${siteUrl}/`,
        logo: `${siteUrl}/icon.svg`,
        description: MARKE_SATZ,
        // sameAs (Social-Media-Profile) erst wieder, wenn Instagram aktiv bespielt wird (12.11.2026)
      },
      {
        "@type": "WebSite",
        "@id": `${siteUrl}/#website`,
        name: SITE_NAME,
        alternateName: "diesdas.events",
        url: `${siteUrl}/`,
        inLanguage: "de-DE",
        publisher: { "@id": `${siteUrl}/#organisation` },
        // Das Suchfeld auf /entdecken schickt genau diesen Parameter (name="q")
        potentialAction: {
          "@type": "SearchAction",
          target: { "@type": "EntryPoint", urlTemplate: `${siteUrl}/entdecken?q={search_term_string}` },
          "query-input": "required name=search_term_string",
        },
      },
    ],
  };
}
/** Vorschaubild für Seiten ohne eigenes Foto (Wortmarke auf Navy, 1200×630) */
export const STANDARD_BILD = { url: "/og-standard.png", width: 1200, height: 630, alt: "dies.das.düsseldorf – Was geht heute in Düsseldorf?" };

type SP = Record<string, string | string[] | undefined>;

/** Hat die URL Parameter (außer den ausdrücklich ignorierten)? */
export function hatParameter(sp: SP, ignorieren: string[] = []): boolean {
  return Object.entries(sp).some(([k, v]) => !ignorieren.includes(k) && v !== undefined && v !== "");
}

export interface SeitenAngaben {
  /** Kanonischer Pfad, z. B. „/heute“ */
  pfad: string;
  /** Titel (läuft durch das Titel-Template des Layouts); weglassen = Standardtitel des Layouts */
  titel?: string;
  beschreibung?: string;
  /** Vorschaubild (absolute oder relative URL) */
  bild?: string | null;
  /** Variante mit Parametern → noindex, follow, ohne Canonical */
  noindex?: boolean;
}

export function seitenMetadaten({ pfad, titel, beschreibung, bild, noindex = false }: SeitenAngaben): Metadata {
  // Eigenes Bild (Event-Foto/Symbolbild – dieselbe URL, die der Mensch sieht), sonst das Standardbild
  const bilder = bild ? [{ url: bild }] : [STANDARD_BILD];
  return {
    ...(titel ? { title: titel } : {}),
    ...(beschreibung ? { description: beschreibung } : {}),
    ...(noindex ? { robots: { index: false, follow: true } } : { alternates: { canonical: pfad } }),
    // Layout-Felder (siteName, locale, type) wiederholen: ein eigenes openGraph-Objekt ersetzt das des Layouts
    openGraph: {
      siteName: SITE_NAME,
      locale: "de_DE",
      type: "website",
      url: pfad,
      ...(titel ? { title: titel } : {}),
      ...(beschreibung ? { description: beschreibung } : {}),
      images: bilder,
    },
    twitter: {
      card: "summary_large_image",
      ...(titel ? { title: titel } : {}),
      ...(beschreibung ? { description: beschreibung } : {}),
      images: [bild ?? STANDARD_BILD.url],
    },
  };
}
