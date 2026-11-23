// Proxy (früher „Middleware“), läuft vor dem Rendern:
//  1. Für lange abgelaufene Events die im Dashboard getroffene SEO-Entscheidung – 301 auf eine interne
//     Seite oder 410 Gone. Ohne Entscheidung (Normalfall) weiter mit 2.
//  2. Echte Statuscodes (lib/pfad-pruefung.ts): 308 von /event/<uuid> und von einer falschen Kategorie auf
//     die kanonische Event-URL, 308 für zum Club umgetypte Orte, 404 für unbekannte Events, Reihen, Tage
//     und Orte. Mit cacheComponents ginge das in der Seite nicht mehr (das Layout streamt vorher → Status 200).
//
// Cache-Control „no-store“ bei den Dashboard-Entscheidungen: Browser und Zwischenspeicher merken sich die
// Antwort nicht. So wirkt das Zurücknehmen einer Entscheidung für Besucher nach spätestens 10 Minuten.
// (Google wertet eine 301 trotzdem als dauerhaft – deshalb nur entscheiden, wenn es dabei bleiben soll.)
import { NextResponse, type NextRequest } from "next/server";
import { entdeckenZiel, pfadPruefen } from "@/lib/pfad-pruefung";
import { seoAktionFuer, seoTabelle, zielAufloesen } from "@/lib/seo-entscheidungen";
import { ADMIN_OFFENE_SEITEN, hatAdminKopf, istAdminBereich, istAdminPfad } from "@/lib/admin/bereich";
import { ADMIN_COOKIE } from "@/lib/admin/konfig";
import { cookieLesen } from "@/lib/konto/cookies";
import { bremsAdresse, BREMSE_FENSTER_MS, gebremst, istGuideUebersicht, sammelGebremst } from "@/lib/bremse";

const GONE_HTML = `<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Event nicht mehr verfügbar · dies.das.düsseldorf</title></head><body style="font-family:system-ui,sans-serif;max-width:560px;margin:15vh auto;padding:0 16px;line-height:1.5;color:#1b2540"><h1>Dieses Event ist nicht mehr verfügbar.</h1><p>Die Seite wurde entfernt, weil das Event schon lange vorbei ist.</p><p><a href="/entdecken" style="color:#457b9d">Aktuelle Events in Düsseldorf entdecken</a></p></body></html>`;

// Eigene 404-Seite direkt aus dem Proxy (wie die 410-Seite). KEIN Rewrite auf eine interne Route: hinter nginx
// (Host localhost:3847, X-Forwarded-Proto https) wird das Rewrite-Ziel zu https://localhost:3847/…, Next hält es
// für eine fremde Adresse, ruft sie per HTTPS ab und antwortet mit 500 (live gemessen am 11.11.2026).
const NICHT_GEFUNDEN_HTML = `<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Seite nicht gefunden · dies.das.düsseldorf</title></head><body style="font-family:system-ui,sans-serif;max-width:560px;margin:15vh auto;padding:0 16px;line-height:1.5;color:#1b2540"><p style="font-style:italic;font-weight:700;font-size:20px;margin:0 0 24px">dies.das.düsseldorf</p><h1>Hier ist nichts los.</h1><p>Die Seite gibt es nicht oder das Event ist schon vorbei.</p><p><a href="/heute" style="color:#457b9d">Was heute in Düsseldorf los ist</a> · <a href="/entdecken" style="color:#457b9d">Alle Events entdecken</a> · <a href="/" style="color:#457b9d">Startseite</a></p></body></html>`;

export async function proxy(request: NextRequest) {
  const pfad = request.nextUrl.pathname;

  // Admin-Bereich (Plan docs/plan-admin-dashboard-2026-11-23.md, 3.2) – VOR allen anderen Zweigen.
  // Den Bereich erkennt nur der Kopf X-DDD-Bereich, den nginx je Website fest setzt (Host ist immer localhost:3847).
  // Startseite: Auf admin.diesdas.events → 308 auf /admin. Weiterleitung wie die übrigen Zweige über
  // NextResponse.redirect(new URL(…, request.url)): Next macht eine Location mit eigenem Ursprung selbst relativ
  // (live gemessen 23.11.2026: /entdecken?kategorie=musik → „location: /kategorie/musik“). Eine von Hand relative
  // Location lehnt der Proxy dagegen mit 500 ab („Invalid URL“, lokal gemessen 23.11.2026).
  // Auf der Website läuft „/“ unverändert weiter, ohne die übrigen Zweige.
  if (pfad === "/") {
    if (hatAdminKopf(request.headers)) {
      const antwort = NextResponse.redirect(new URL("/admin", request.url), 308);
      antwort.headers.set("Cache-Control", "no-store");
      return antwort;
    }
    return NextResponse.next();
  }
  if (istAdminPfad(pfad)) {
    // Ohne den Admin-Kopf gibt es den Bereich nicht: echte 404, auch auf der öffentlichen Website
    if (!istAdminBereich(request.headers)) {
      return new NextResponse(NICHT_GEFUNDEN_HTML, {
        status: 404,
        headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
      });
    }
    // Seiten ohne Admin-Cookie gleich zur Anmeldung (Bequemlichkeit; die Daten schützt erst /api/admin)
    if (!pfad.startsWith("/api/") && !ADMIN_OFFENE_SEITEN.has(pfad) && !cookieLesen(request.headers, ADMIN_COOKIE)) {
      const antwort = NextResponse.redirect(new URL("/admin/anmelden", request.url), 307);
      antwort.headers.set("Cache-Control", "no-store");
      return antwort;
    }
    const antwort = NextResponse.next();
    antwort.headers.set("Cache-Control", "private, no-store");
    antwort.headers.set("Referrer-Policy", "no-referrer");
    antwort.headers.set("X-Robots-Tag", "noindex, nofollow");
    return antwort;
  }

  // Bremse gegen Massenabrufe der Guides (Ausfall 23.11.2026: ~3.000 Abrufe von /guides/restaurants-cafes durch einen
  // einzelnen Client, Speicherüberlauf alle ~40 s). Vor jeder Rechnung: zu viele Aufrufe derselben Adresse → 429.
  if (pfad === "/guides" || pfad.startsWith("/guides/")) {
    if (gebremst(bremsAdresse(request.headers))) {
      return new NextResponse("Zu viele Anfragen. Bitte in einer Minute noch einmal versuchen.", {
        status: 429,
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "no-store",
          "Retry-After": String(Math.ceil(BREMSE_FENSTER_MS / 1000)),
        },
      });
    }
    // Gemeinsame Grenze je Übersicht über alle Adressen (die Abrufe kamen von über 1.300 Adressen)
    if (istGuideUebersicht(pfad) && sammelGebremst(pfad)) {
      return new NextResponse("Gerade ist hier sehr viel los. Bitte in einer Minute noch einmal versuchen.", {
        status: 503,
        headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", "Retry-After": "30" },
      });
    }
  }

  // Ein einzelner Kategorie- oder Stadtteil-Filter ist die Landingpage → 301 (Filter mit mehr Parametern bleiben noindex)
  if (pfad === "/entdecken") {
    const ziel = entdeckenZiel(request.nextUrl.searchParams);
    return ziel ? NextResponse.redirect(new URL(ziel, request.url), 301) : NextResponse.next();
  }

  const aktion = seoAktionFuer(pfad, await seoTabelle());
  if (aktion?.aktion === "weiterleiten") {
    const ziel = zielAufloesen(aktion.ziel, request.url);
    if (ziel) {
      const antwort = NextResponse.redirect(ziel, 301);
      antwort.headers.set("Cache-Control", "no-store");
      return antwort;
    }
  } else if (aktion?.aktion === "gone") {
    return new NextResponse(GONE_HTML, {
      status: 410,
      headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
    });
  }

  const pruefung = await pfadPruefen(pfad, request.nextUrl.searchParams);
  if (pruefung.art === "umleiten") {
    const ziel = new URL(pruefung.ziel, request.url);
    ziel.search = request.nextUrl.search;
    return NextResponse.redirect(ziel, 308);
  }
  if (pruefung.art === "fehlt") {
    return new NextResponse(NICHT_GEFUNDEN_HTML, {
      status: 404,
      headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
    });
  }
  // Magazin-Vorschau (Plan Redaktion 5.3): Schlüssel steht in der URL – nicht zwischenspeichern, nicht weitergeben
  if (pfad.startsWith("/magazin/vorschau/")) {
    const antwort = NextResponse.next();
    antwort.headers.set("Cache-Control", "private, no-store");
    antwort.headers.set("Referrer-Policy", "no-referrer");
    antwort.headers.set("X-Robots-Tag", "noindex, nofollow");
    return antwort;
  }
  return NextResponse.next();
}

export const config = {
  // Eventseiten (auch /event/<uuid>), Tage, Reihen, Guide-Orte, Landingpages, /entdecken (301 für Einzelfilter),
  // Magazin (Plan Redaktion T4: /magazin/:path* trifft auch /magazin selbst) und /feed.xml (308 auf den Magazin-Feed)
  matcher: [
    // Guides: alle Pfade (auch die Hub-Seiten selbst) – wegen der Bremse gegen Massenabrufe (23.11.2026)
    "/event/:path*", "/tag/:datum", "/reihe/:slug", "/guides", "/guides/:path*", "/kategorie/:slug",
    "/kategorie/:slug/:unter", "/stadtteil/:slug", "/entdecken", "/magazin/:path*", "/feed.xml",
    // Ortsseiten (Plan Locations 3.10): aktive Spielstätte 200, Guide-Slug 308 auf die kanonische Guide-URL,
    // alter Slug 308 über ort_weiterleitungen, sonst echte 404. /orte selbst ist die Übersicht (immer 200).
    "/orte/:path+",
    // Admin-Bereich (Plan Admin-Dashboard 3.2): Startseite (308 nur mit Admin-Kopf), Seiten und API.
    // /_next und Bildpfade bleiben bewusst außerhalb, damit die Website nicht langsamer wird.
    "/", "/admin/:path*", "/api/admin/:path*",
  ],
};
