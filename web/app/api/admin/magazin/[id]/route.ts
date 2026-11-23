// Admin-Bereich – ein Magazin-Beitrag (Plan Admin-Dashboard 4.6, Stufe 2).
// GET                                   → Beitrag (ohne Vorschau-Hash)
// POST { aktion: "speichern", felder }  → Eingaben prüfen, Prüfung (a)–(i) neu, admin_magazin_speichern
// POST { aktion: "pruefen" }            → nur neu prüfen (z. B. nachdem ein Event abgesagt wurde)
// POST { aktion: "veroeffentlichen" | "zurueckziehen" }
// POST { aktion: "korrektur", hinweis, inhalt_md? } → veröffentlichten Beitrag korrigieren (immer mit Hinweis)
import { revalidateTag } from "next/cache";
import type { SupabaseClient } from "@supabase/supabase-js";
import { magazinEingabe } from "@/lib/admin/magazin";
import { eingebetteteEvents, magazinPruefen, type PruefEingabe } from "@/lib/admin/magazin-pruefung";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { MAGAZIN_CACHE_TAG } from "@/lib/magazin-daten";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

async function eventStatus(db: SupabaseClient, ids: string[]) {
  const status = new Map<string, { abgelehnt: boolean; abgesagt: boolean }>();
  if (!ids.length) return status;
  const { data } = await db.from("events").select("id, abgelehnt, abgesagt").in("id", ids);
  for (const z of data ?? []) status.set(String(z.id).toLowerCase(), { abgelehnt: !!z.abgelehnt, abgesagt: !!z.abgesagt });
  return status;
}

async function beitragLaden(db: SupabaseClient, id: string) {
  const { data, error } = await db.rpc("admin_magazin_beitrag", { p_id: id });
  if (error) throw new Error(error.message);
  return data as Record<string, unknown>;
}

function pruefEingabe(b: Record<string, unknown>): PruefEingabe {
  const s = (w: unknown) => (typeof w === "string" ? w : null);
  return {
    rubrik: String(b.rubrik ?? ""),
    titel: String(b.titel ?? ""),
    teaser: s(b.teaser),
    kurzfassung: Array.isArray(b.kurzfassung) ? (b.kurzfassung as unknown[]).map(String) : null,
    faq: Array.isArray(b.faq) ? (b.faq as { frage?: unknown; antwort?: unknown }[]) : null,
    inhalt_md: String(b.inhalt_md ?? ""),
    hero_bild: s(b.hero_bild),
    hero_alt: s(b.hero_alt),
    gueltig_von: s(b.gueltig_von),
    gueltig_bis: s(b.gueltig_bis),
  };
}

export async function GET(request: Request, ctx: RouteContext<"/api/admin/magazin/[id]">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    try {
      return adminAntwort(200, { beitrag: await beitragLaden(admin!.db, id) }, setCookies);
    } catch (e) {
      return adminAntwort(404, { fehler: e instanceof Error ? e.message : "Nicht gefunden." }, setCookies);
    }
  });
}

export async function POST(request: Request, ctx: RouteContext<"/api/admin/magazin/[id]">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const db = admin!.db;
    const fehler = (e: { message: string }) => adminAntwort(400, { fehler: e.message, code: "db" }, setCookies);

    if (body.aktion === "speichern" || body.aktion === "pruefen") {
      const eingabe = body.aktion === "speichern" && body.felder && typeof body.felder === "object" ? (body.felder as Record<string, unknown>) : {};
      const geprueft = magazinEingabe(eingabe);
      if (!geprueft.ok) return adminAntwort(400, { fehler: geprueft.fehler, code: "eingabe" }, setCookies);
      let bisher: Record<string, unknown>;
      try {
        bisher = await beitragLaden(db, id);
      } catch (e) {
        return adminAntwort(404, { fehler: e instanceof Error ? e.message : "Nicht gefunden." }, setCookies);
      }
      const neu = { ...bisher, ...geprueft.felder };
      const pe = pruefEingabe(neu);
      const pruefung = magazinPruefen(pe, await eventStatus(db, eingebetteteEvents(pe.inhalt_md)));
      const { data, error } = await db.rpc("admin_magazin_speichern", { p_id: id, p_felder: geprueft.felder, p_pruefung: pruefung });
      if (error) return fehler(error);
      return adminAntwort(200, { ok: true, pruefung, ergebnis: data }, setCookies);
    }

    if (body.aktion === "veroeffentlichen" || body.aktion === "zurueckziehen") {
      const { data, error } = await db.rpc(body.aktion === "veroeffentlichen" ? "admin_magazin_veroeffentlichen" : "admin_magazin_zurueckziehen", { p_id: id });
      if (error) return fehler(error);
      revalidateTag(MAGAZIN_CACHE_TAG, { expire: 0 });
      return adminAntwort(200, { ok: true, ergebnis: data }, setCookies);
    }

    if (body.aktion === "korrektur") {
      const hinweis = typeof body.hinweis === "string" ? body.hinweis : "";
      const inhalt = typeof body.inhalt_md === "string" ? body.inhalt_md : null;
      const { data, error } = await db.rpc("admin_magazin_korrektur", { p_id: id, p_hinweis: hinweis, p_inhalt_md: inhalt });
      if (error) return fehler(error);
      revalidateTag(MAGAZIN_CACHE_TAG, { expire: 0 });
      return adminAntwort(200, { ok: true, ergebnis: data }, setCookies);
    }

    return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);
  });
}
