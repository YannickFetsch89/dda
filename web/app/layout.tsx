import type { Metadata, Viewport } from "next";
import { DM_Serif_Display, Inter } from "next/font/google";
import { DetailsVerhalten, TabBar } from "@/components/client";
import { CookieBanner } from "@/components/cookie-banner";
import { DatenHinweis, Fuss, KategorieLeiste, Kopf } from "@/components/rahmen";
import "./globals.css";

const dmSerif = DM_Serif_Display({ variable: "--font-dm-serif", subsets: ["latin"], weight: "400", style: ["normal", "italic"] });
const inter = Inter({ variable: "--font-inter", subsets: ["latin"], weight: ["400", "500", "600", "700", "800", "900"] });

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? "https://diesdas.events"),
  title: { default: "dies.das.düsseldorf – Was geht heute in Düsseldorf?", template: "%s · dies.das.düsseldorf" },
  description: "Alle Events in Düsseldorf, jeden Tag neu gesammelt: Konzerte, Kultur, Food, Nightlife, Familie und mehr – nach Tag, Kategorie und Stadtteil.",
  openGraph: { siteName: "dies.das.düsseldorf", locale: "de_DE", type: "website" },
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
    <html lang="de" className={`${dmSerif.variable} ${inter.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
        {/* Material Symbols Rounded (Icons laut Brand Identity) */}
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0..1,0&display=swap" />
      </head>
      <body>
        <DatenHinweis />
        <Kopf />
        <KategorieLeiste />
        <main>{children}</main>
        <Fuss />
        <TabBar />
        <DetailsVerhalten />
        <CookieBanner />
      </body>
    </html>
  );
}
