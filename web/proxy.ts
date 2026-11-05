// Proxy (früher „Middleware“): liefert für lange abgelaufene Events die im Dashboard getroffene
// SEO-Entscheidung aus – 301 auf eine interne Seite oder 410 Gone. Ohne Entscheidung (Normalfall)
// läuft die Anfrage unverändert zur Eventseite (HTTP 200).
import { NextResponse, type NextRequest } from "next/server";
import { seoAktionFuer, seoTabelle } from "@/lib/seo-entscheidungen";

const GONE_HTML = `<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Event nicht mehr verfügbar · dies.das.düsseldorf</title></head><body style="font-family:system-ui,sans-serif;max-width:560px;margin:15vh auto;padding:0 16px;line-height:1.5;color:#1b2540"><h1>Dieses Event ist nicht mehr verfügbar.</h1><p>Die Seite wurde entfernt, weil das Event schon lange vorbei ist.</p><p><a href="/entdecken" style="color:#457b9d">Aktuelle Events in Düsseldorf entdecken</a></p></body></html>`;

export async function proxy(request: NextRequest) {
  const aktion = seoAktionFuer(request.nextUrl.pathname, await seoTabelle());
  if (!aktion) return NextResponse.next();
  if (aktion.aktion === "weiterleiten") {
    return NextResponse.redirect(new URL(aktion.ziel, request.url), 301);
  }
  return new NextResponse(GONE_HTML, {
    status: 410,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=3600" },
  });
}

export const config = {
  // Nur Eventseiten /event/<kategorie>/<slug>
  matcher: "/event/:kategorie/:slug",
};
