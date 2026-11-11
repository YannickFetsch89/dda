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
import { pfadPruefen } from "@/lib/pfad-pruefung";
import { seoAktionFuer, seoTabelle, zielAufloesen } from "@/lib/seo-entscheidungen";

const GONE_HTML = `<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Event nicht mehr verfügbar · dies.das.düsseldorf</title></head><body style="font-family:system-ui,sans-serif;max-width:560px;margin:15vh auto;padding:0 16px;line-height:1.5;color:#1b2540"><h1>Dieses Event ist nicht mehr verfügbar.</h1><p>Die Seite wurde entfernt, weil das Event schon lange vorbei ist.</p><p><a href="/entdecken" style="color:#457b9d">Aktuelle Events in Düsseldorf entdecken</a></p></body></html>`;

/** Interner Pfad ohne Route: Next rendert dort not-found.tsx mit echtem Status 404. */
const NICHT_GEFUNDEN = "/__nicht-gefunden";

export async function proxy(request: NextRequest) {
  const pfad = request.nextUrl.pathname;

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

  const pruefung = await pfadPruefen(pfad);
  if (pruefung.art === "umleiten") {
    const ziel = new URL(pruefung.ziel, request.url);
    ziel.search = request.nextUrl.search;
    return NextResponse.redirect(ziel, 308);
  }
  if (pruefung.art === "fehlt") {
    return NextResponse.rewrite(new URL(NICHT_GEFUNDEN, request.url));
  }
  return NextResponse.next();
}

export const config = {
  // Eventseiten (auch /event/<uuid>), Tage, Reihen und Guide-Orte
  matcher: ["/event/:path*", "/tag/:datum", "/reihe/:slug", "/guides/:hub/:slug"],
};
