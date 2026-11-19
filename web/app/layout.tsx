import type { Metadata, Viewport } from "next";
import { markeJsonLd, ROBOTS_INDEX, seitenAlternates, STANDARD_BILD } from "@/lib/seo";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";
import { DM_Serif_Display, Inter } from "next/font/google";
import localFont from "next/font/local";
import { DetailsVerhalten, TabBar } from "@/components/client";
import { CookieBanner } from "@/components/cookie-banner";
import { KontoSync, MerkHinweis } from "@/components/konto";
import { kontenAktiv } from "@/lib/konto/konfig";
import { DatenHinweis, Fuss, KategorieLeiste, Kopf } from "@/components/rahmen";
import { jsonLdText } from "@/lib/json-ld";
import "./globals.css";

const dmSerif = DM_Serif_Display({ variable: "--font-dm-serif", subsets: ["latin"], weight: "400", style: ["normal", "italic"] });
const inter = Inter({ variable: "--font-inter", subsets: ["latin"], weight: ["400", "500", "600", "700", "800", "900"] });
// Icon-Schrift (Material Symbols Rounded, Apache 2.0) vom eigenen Server statt von fonts.googleapis.com –
// so geht beim Seitenaufruf keine IP-Adresse an Google. "block" verhindert, dass kurz Icon-Namen als Text erscheinen.
const icons = localFont({
  src: "./fonts/material-symbols-rounded.woff2",
  variable: "--font-icons",
  weight: "400",
  style: "normal",
  display: "block",
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? "https://diesdas.events"),
  title: { default: "dies.das.düsseldorf – Was geht heute in Düsseldorf?", template: "%s · dies.das.düsseldorf" },
  description: "Alle Events in Düsseldorf, jeden Tag neu gesammelt: Konzerte, Kultur, Food, Nightlife, Familie und mehr – nach Tag, Kategorie und Stadtteil.",
  openGraph: { siteName: "dies.das.düsseldorf", locale: "de_DE", type: "website", images: [STANDARD_BILD] },
  twitter: { card: "summary_large_image", images: [STANDARD_BILD.url] },
  // Große Bildvorschau erlauben (Google Discover zeigt sonst nur ein kleines Vorschaubild) und Snippets nicht kürzen.
  // Seiten mit eigenem robots (z. B. noindex bei Filtern, Konto-Seiten) ersetzen diesen Wert ganz.
  robots: ROBOTS_INDEX,
  // Feed-Link des Magazins für Seiten ohne eigenes alternates (Plan Redaktion 5.6); erst mit dem Livegang
  ...(MAGAZIN_VERLINKT ? { alternates: seitenAlternates() } : {}),
  // Google Search Console (HTML-Tag-Methode); Token kommt aus .env.local, wird beim Build eingesetzt
  verification: process.env.GOOGLE_SITE_VERIFICATION ? { google: process.env.GOOGLE_SITE_VERIFICATION } : undefined,
};

export const viewport: Viewport = {
  themeColor: "#1B2540",
};

// Theme vor dem ersten Paint setzen: gespeicherte Wahl, sonst prefers-color-scheme
const THEME_SCRIPT = `try{var t=localStorage.getItem('ddd-theme');if(!t){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="de" className={`${dmSerif.variable} ${inter.variable} ${icons.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(markeJsonLd(process.env.SITE_URL ?? "https://diesdas.events")) }} />
      </head>
      {/* data-konten: Schalter KONTEN_AKTIV beim Build, für Client-Bausteine (Hinweis nach dem ersten Merken) */}
      <body data-konten={kontenAktiv() ? "1" : undefined}>
        <DatenHinweis />
        <Kopf />
        <KategorieLeiste />
        <main>{children}</main>
        <Fuss />
        <TabBar />
        <DetailsVerhalten />
        {kontenAktiv() && (
          <>
            <KontoSync />
            <MerkHinweis />
          </>
        )}
        <CookieBanner />
      </body>
    </html>
  );
}
