// Einheitliche Seiten-Metadaten (SEO-/GEO-Plan Nov. 2026, Maßnahme 2): Canonical, Open Graph und Twitter
// aus einer Hand. metadataBase steht im Layout – Pfade bleiben relativ.
//
// Regel: Eine indexierbare Seite kanonisiert auf sich selbst. Varianten mit Filter-/Such-Parametern bekommen
// „noindex, follow“ und KEIN Canonical auf eine andere URL – beides zusammen wären widersprüchliche Signale.
import type { Metadata } from "next";

export const SITE_NAME = "dies.das.düsseldorf";

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
  const bilder = bild ? [{ url: bild }] : undefined;
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
      ...(bilder ? { images: bilder } : {}),
    },
    twitter: {
      card: bild ? "summary_large_image" : "summary",
      ...(titel ? { title: titel } : {}),
      ...(beschreibung ? { description: beschreibung } : {}),
      ...(bild ? { images: [bild] } : {}),
    },
  };
}
