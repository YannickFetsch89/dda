// Admin-Bereich – SEO-Aufräumen (Plan Admin-Dashboard 4.10, Stufe 5b; Umzug aus dashboard/seo_aufraeumen.py).
// GET ?offen=1                          → Kennzahlen und die ältesten 500 (offenen) Kandidaten mit Entscheidung
// GET ?export=1&offen=1                 → CSV derselben Liste (für den Abgleich mit der Search Console)
// POST { aktion: "entscheiden", ids, art }  → event_seo_entscheidungen (Policies „Admins entscheiden/ändern SEO“)
// POST { aktion: "zuruecknehmen", ids }      → Entscheidungen löschen
// Die Website liest die Tabelle alle 10 Minuten neu (lib/seo-entscheidungen.ts).
import type { SupabaseClient } from "@supabase/supabase-js";
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { abgelaufenFilter, csvFeld, entscheidungenBauen, eventPfadSeo, reiheSlug, SEO_AKTIONEN, webKategorie, type SeoArt, type SeoEvent } from "@/lib/admin/seo";
import { heuteBerlin } from "@/lib/datum";

const SEITE = 1000;
const ANZEIGE_MAX = 500;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

async function alle<T>(abfrage: (von: number, bis: number) => PromiseLike<{ data: T[] | null; error: { message: string } | null }>): Promise<T[]> {
  const ergebnis: T[] = [];
  for (let seite = 0; seite < 500; seite++) {
    const { data, error } = await abfrage(seite * SEITE, seite * SEITE + SEITE - 1);
    if (error) throw new Error(error.message);
    ergebnis.push(...(data ?? []));
    if ((data ?? []).length < SEITE) break;
  }
  return ergebnis;
}

/**
 * Kennzahlen und Liste (Cursor-Gesamtprüfung, gering: vorher wurden zum Zählen alle abgelaufenen Event-IDs geladen,
 * bis zu 500.000 Zeilen im Website-Prozess). Jetzt: „gesamt“ zählt die Datenbank (count, head), die Entscheidungen
 * (kleine Tabelle) werden geladen und ihre noch passenden Events stückweise gezählt; die Liste bricht nach
 * ANZEIGE_MAX Einträgen, MAX_SEITEN Seiten oder MAX_MS ab.
 */
const MAX_SEITEN = 20;
const MAX_MS = 4000;

async function laden(db: SupabaseClient, nurOffen: boolean) {
  const start = Date.now();
  const filter = abgelaufenFilter(heuteBerlin(new Date()));
  const kandidaten = () => db.from("events").select("id", { count: "exact", head: true }).eq("abgelehnt", false).not("slug", "is", null).or(filter);
  const { count: gesamt, error: fGesamt } = await kandidaten();
  if (fGesamt) throw new Error(fGesamt.message);
  const entscheidungen = new Map(
    (await alle<{ event_id: string; aktion: string; ziel: string | null }>((a, b) => db.from("event_seo_entscheidungen").select("event_id, aktion, ziel").order("event_id").range(a, b))).map((z) => [z.event_id, z]),
  );
  let entschieden = 0;
  const ids = [...entscheidungen.keys()];
  for (let i = 0; i < ids.length; i += 200) {
    const { count, error } = await kandidaten().in("id", ids.slice(i, i + 200));
    if (error) throw new Error(error.message);
    entschieden += count ?? 0;
  }
  const liste: SeoEvent[] = [];
  let mehr = false;
  for (let seite = 0; liste.length < ANZEIGE_MAX; seite++) {
    if (seite >= MAX_SEITEN || Date.now() - start > MAX_MS) {
      mehr = true;
      break;
    }
    // Nur offene: entschiedene Events schon in der Datenbank ausnehmen (Anti-Join über die Einbettung; Cursor-
    // Prüfung 24.11.2026 – sonst konnten 20 Seiten voller entschiedener Events die offenen verdecken)
    let abfrage = db
      .from("events")
      .select(nurOffen ? "id, titel, datum, datum_bis, ort, kategorie, slug, reihe:reihen(slug), seo:event_seo_entscheidungen!left(event_id)" : "id, titel, datum, datum_bis, ort, kategorie, slug, reihe:reihen(slug)")
      .eq("abgelehnt", false)
      .not("slug", "is", null)
      .or(filter);
    if (nurOffen) abfrage = abfrage.is("seo", null);
    const { data, error } = await abfrage
      .order("datum")
      .order("id")
      .range(seite * SEITE, seite * SEITE + SEITE - 1);
    if (error) throw new Error(error.message);
    for (const e of (data ?? []) as unknown as SeoEvent[]) {
      if (nurOffen && entscheidungen.has(e.id)) continue;
      if (liste.length >= ANZEIGE_MAX) {
        mehr = true;
        break;
      }
      liste.push(e);
    }
    if ((data ?? []).length < SEITE) break;
  }
  return { entscheidungen, gesamt: gesamt ?? 0, entschieden, liste, mehr };
}

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const p = new URL(request.url).searchParams;
    const nurOffen = p.get("offen") !== "0";
    try {
      const d = await laden(admin!.db, nurOffen);
      const zeilen = d.liste.map((e) => ({
        id: e.id,
        datum: e.datum,
        titel: e.titel,
        ort: e.ort,
        kategorie: webKategorie(e.kategorie),
        reihe: reiheSlug(e),
        pfad: eventPfadSeo(e),
        entscheidung: d.entscheidungen.get(e.id)?.aktion ?? null,
        ziel: d.entscheidungen.get(e.id)?.ziel ?? null,
      }));
      if (p.get("export") === "1") {
        const kopf = ["url", "titel", "datum", "ort", "kategorie", "reihe", "aktion", "ziel"];
        const csv = [kopf.join(";"), ...zeilen.map((z) => [`https://diesdas.events${z.pfad}`, z.titel, z.datum, z.ort, z.kategorie, z.reihe, z.entscheidung, z.ziel].map(csvFeld).join(";"))].join("\r\n");
        const antwort = new Response("﻿" + csv + "\r\n", {
          headers: {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": `attachment; filename="seo-kandidaten-${heuteBerlin(new Date())}.csv"`,
            "Cache-Control": "private, no-store",
          },
        });
        for (const c of setCookies) antwort.headers.append("Set-Cookie", c);
        return antwort;
      }
      return adminAntwort(200, { gesamt: d.gesamt, entschieden: d.entschieden, offen: d.gesamt - d.entschieden, mehr: d.mehr, zeilen, aktionen: SEO_AKTIONEN }, setCookies);
    } catch (e) {
      return adminAntwort(500, { fehler: e instanceof Error ? e.message : "Nicht ladbar." }, setCookies);
    }
  });
}

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    const db = admin!.db;
    const ids = Array.isArray(body.ids) ? [...new Set(body.ids.filter((x): x is string => typeof x === "string" && UUID.test(x)))] : [];
    if (!ids.length || ids.length > 1000) return adminAntwort(400, { fehler: "1 bis 1.000 Events auswählen." }, setCookies);
    if (body.aktion === "zuruecknehmen") {
      for (let i = 0; i < ids.length; i += 200) {
        const { error } = await db.from("event_seo_entscheidungen").delete().in("event_id", ids.slice(i, i + 200));
        if (error) return adminAntwort(500, { fehler: error.message }, setCookies);
      }
      await protokollieren(db, { aktion: "seo_zuruecknehmen", tabelle: "event_seo_entscheidungen", nachher: { anzahl: ids.length } });
      return adminAntwort(200, { ok: true, anzahl: ids.length }, setCookies);
    }
    if (body.aktion !== "entscheiden" || typeof body.art !== "string" || !(body.art in SEO_AKTIONEN)) return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);
    const events: SeoEvent[] = [];
    for (let i = 0; i < ids.length; i += 200) {
      const { data, error } = await db.from("events").select("id, titel, datum, datum_bis, ort, kategorie, slug, reihe:reihen(slug)").in("id", ids.slice(i, i + 200)).not("slug", "is", null);
      if (error) return adminAntwort(500, { fehler: error.message }, setCookies);
      events.push(...((data ?? []) as unknown as SeoEvent[]));
    }
    const { zeilen, uebersprungen } = entscheidungenBauen(events, body.art as SeoArt, admin!.sitzung.nutzerId, new Date().toISOString());
    for (let i = 0; i < zeilen.length; i += 500) {
      const { error } = await db.from("event_seo_entscheidungen").upsert(zeilen.slice(i, i + 500), { onConflict: "event_id" });
      if (error) return adminAntwort(500, { fehler: error.message }, setCookies);
    }
    await protokollieren(db, { aktion: "seo_entscheiden", tabelle: "event_seo_entscheidungen", nachher: { art: body.art, anzahl: zeilen.length, uebersprungen: uebersprungen.length } });
    return adminAntwort(200, { ok: true, anzahl: zeilen.length, uebersprungen: uebersprungen.length }, setCookies);
  });
}
