// Admin-Bereich – gemeinsamer Rahmen für alle Routen unter /api/admin (Plan Admin-Dashboard 3.3).
// Reihenfolge: Bereich → (POST: Origin → JSON → Größe → Body) → Sitzung/Rolle/Zwei-Faktor → Route.
// Bewusst NICHT kontoRoute: Die hängt am Schalter KONTEN_AKTIV und am Konto-Ablauf (Cursor-Prüfung 1, Befund 8).
import "server-only";
import { absenderIp, zuGross } from "../formulare";
import { istLokal } from "../konto/cookies";
import { istAdminBereich } from "./bereich";
import { ADMIN_BODY_MAX_BYTES } from "./konfig";
import { adminOriginErlaubt } from "./pruefungen";
import { adminSitzung, type AdminSitzung } from "./sitzung";

export interface AdminKontext {
  request: Request;
  ip: string;
  lokal: boolean;
  body: Record<string, unknown>;
  /** Nur bei Routen mit Anmeldung gesetzt */
  admin: AdminSitzung | null;
  /** Zusätzliche Set-Cookie-Zeilen (Anmelden, Abmelden, erneuerte Tokens) */
  setCookies: string[];
}

export interface AdminRouteOptionen {
  /** Braucht eine gültige Admin-Sitzung (Standard: ja) */
  anmeldung?: boolean;
  /** Verlangt Zwei-Faktor-Stufe aal2 (Standard: ja) */
  zweiFaktor?: boolean;
}

/** JSON-Antwort mit den Köpfen des Admin-Bereichs */
export function adminAntwort(status: number, daten: unknown, setCookies: string[] = []): Response {
  const kopf = new Headers({
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "private, no-store",
    "X-Robots-Tag": "noindex, nofollow",
    "Referrer-Policy": "no-referrer",
  });
  for (const c of setCookies) kopf.append("Set-Cookie", c);
  return new Response(JSON.stringify(daten), { status, headers: kopf });
}

export async function adminRoute(
  request: Request,
  optionen: AdminRouteOptionen,
  handler: (ctx: AdminKontext) => Promise<Response>,
): Promise<Response> {
  const { anmeldung = true, zweiFaktor = true } = optionen;
  // Ohne den Kopf von admin.diesdas.events gibt es den Bereich nicht (proxy.ts prüft das schon, hier die zweite Sicherung)
  if (!istAdminBereich(request.headers)) return new Response("Nicht gefunden", { status: 404 });

  const ctx: AdminKontext = {
    request,
    ip: absenderIp(request.headers),
    lokal: istLokal(request.headers),
    body: {},
    admin: null,
    setCookies: [],
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    if (!adminOriginErlaubt(request.headers)) return adminAntwort(403, { fehler: "Ungültiger Ursprung.", code: "origin" });
    if (!(request.headers.get("content-type") ?? "").toLowerCase().startsWith("application/json")) {
      return adminAntwort(415, { fehler: "Nur JSON.", code: "format" });
    }
    if (zuGross(request, ADMIN_BODY_MAX_BYTES)) return adminAntwort(413, { fehler: "Anfrage zu groß.", code: "groesse" });
    try {
      const roh = await request.json();
      if (!roh || typeof roh !== "object" || Array.isArray(roh)) throw new Error("kein Objekt");
      ctx.body = roh as Record<string, unknown>;
    } catch {
      return adminAntwort(400, { fehler: "Ungültige Anfrage.", code: "body" });
    }
  }

  if (anmeldung) {
    const s = await adminSitzung(request, zweiFaktor);
    if (!s.ok) {
      const text = { abgemeldet: "Bitte anmelden.", kein_admin: "Kein Admin-Zugang.", zwei_faktor: "Zwei-Faktor-Code nötig.", dienst: "Dienst nicht erreichbar." }[s.code];
      return adminAntwort(s.status, { fehler: text, code: s.code }, s.setCookies);
    }
    ctx.admin = s.admin;
    ctx.setCookies.push(...s.admin.setCookies);
  }

  try {
    return await handler(ctx);
  } catch (e) {
    console.error("Admin-Route fehlgeschlagen:", e);
    return adminAntwort(500, { fehler: "Interner Fehler.", code: "intern" }, ctx.setCookies);
  }
}
