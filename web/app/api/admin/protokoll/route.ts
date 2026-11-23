// Admin-Bereich – Protokoll (Plan Admin-Dashboard 4.10, Stufe 5a). Liest admin_protokoll (Policy: nur Admins).
// GET ?aktion=<Anfang>&tabelle=&seite=        → Einträge, neueste zuerst, 50 je Seite
// POST { aktion: "rueckgaengig", id }         → einfache Feldänderung (event_bearbeiten, ort_bearbeiten) zurücknehmen,
//                                               nur wenn die Felder seitdem nicht noch einmal geändert wurden
import { revalidateTag } from "next/cache";
import { eingabenPruefen, updateBauen, type EventZeile } from "@/lib/admin/events";
import { aenderungen, stammdatenPruefen, STAMMDATEN_FELDER } from "@/lib/admin/orte";
import { protokollieren } from "@/lib/admin/protokoll";
import { rueckgaengigPlan, type ProtokollEintrag } from "@/lib/admin/rueckgaengig";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { EVENTS_CACHE_TAG } from "@/lib/daten";
import { ORTE_CACHE_TAG } from "@/lib/orte";
import { orteZwischenspeicherVerwerfen } from "@/lib/pfad-pruefung";

const SEITE = 50;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const EVENT_SPALTEN =
  "id, slug, titel, datum, datum_bis, uhrzeit, ort, adresse, stadtteil, kategorie, unterkategorie, preis, beschreibung, " +
  "bild_url, ort_id, quelle_name, quelle_url, abgelehnt, abgesagt, nicht_empfehlen, tipp_des_tages, highlight_der_woche, " +
  "top_event_des_monats, erstellt_am, redaktion_felder, abgleich_titel, abgleich_datum, abgleich_uhrzeit, abgleich_ort";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const p = new URL(request.url).searchParams;
    const seite = Math.max(0, Math.min(500, Number(p.get("seite")) || 0));
    let q = admin!.db.from("admin_protokoll").select("id, zeitpunkt, admin_id, aktion, tabelle, ziel_id, vorher, nachher", { count: "exact" });
    const aktion = p.get("aktion")?.trim().replace(/[^a-z_]/g, "").slice(0, 40);
    if (aktion) q = q.like("aktion", `${aktion}%`);
    const tabelle = p.get("tabelle")?.trim().replace(/[^a-z_]/g, "").slice(0, 40);
    if (tabelle) q = q.eq("tabelle", tabelle);
    const ziel = p.get("ziel")?.trim();
    if (ziel && UUID.test(ziel)) q = q.eq("ziel_id", ziel.toLowerCase());
    const { data, count, error } = await q.order("zeitpunkt", { ascending: false }).range(seite * SEITE, seite * SEITE + SEITE - 1);
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    return adminAntwort(200, { seite, proSeite: SEITE, gesamt: count ?? 0, eintraege: data ?? [] }, setCookies);
  });
}

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    if (body.aktion !== "rueckgaengig") return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);
    const id = typeof body.id === "string" ? body.id : "";
    if (!UUID.test(id)) return adminAntwort(400, { fehler: "Ungültiger Eintrag." }, setCookies);
    const db = admin!.db;
    const { data: e, error } = await db.from("admin_protokoll").select("id, aktion, tabelle, ziel_id, vorher, nachher").eq("id", id).maybeSingle();
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    if (!e) return adminAntwort(404, { fehler: "Eintrag nicht gefunden." }, setCookies);
    const eintrag = e as ProtokollEintrag;
    const ziel = eintrag.ziel_id && UUID.test(eintrag.ziel_id) ? eintrag.ziel_id : null;
    if (!ziel) return adminAntwort(400, { fehler: "Diese Aktion lässt sich nicht automatisch rückgängig machen." }, setCookies);

    if (eintrag.aktion === "event_bearbeiten") {
      const { data: aktuell } = await db.from("events").select(EVENT_SPALTEN).eq("id", ziel).maybeSingle();
      const plan = rueckgaengigPlan(eintrag, aktuell as unknown as Record<string, unknown> | null);
      if (!plan.ok) return adminAntwort(409, { fehler: plan.fehler }, setCookies);
      const pruefung = eingabenPruefen(plan.felder);
      if (!pruefung.ok) return adminAntwort(400, { fehler: pruefung.fehler }, setCookies);
      const { update, geaendert } = updateBauen(aktuell as unknown as EventZeile, pruefung.felder);
      if (!geaendert.length) return adminAntwort(200, { ok: true, geaendert: [] }, setCookies);
      let q = db.from("events").update(update).eq("id", ziel);
      for (const [f, w] of plan.erwartet) q = w === null ? q.is(f, null) : q.eq(f, w as string | number | boolean);
      const { data: getroffen, error: f2 } = await q.select("id");
      if (f2) return adminAntwort(f2.code === "23505" ? 409 : 500, { fehler: f2.code === "23505" ? "Rückgängig ergäbe eine Dublette (gleicher Titel, Tag, Ort, Uhrzeit)." : f2.message }, setCookies);
      if (!getroffen?.length) return adminAntwort(409, { fehler: "Gerade eben anders geändert – bitte neu laden und von Hand prüfen." }, setCookies);
      await protokollieren(db, { aktion: "event_rueckgaengig", tabelle: "events", ziel_id: ziel, vorher: eintrag.nachher, nachher: { ...update, protokoll: id } });
      revalidateTag(EVENTS_CACHE_TAG, { expire: 0 });
      if (geaendert.includes("bild_url")) revalidateTag(`event-bild-${ziel}`, { expire: 0 });
      return adminAntwort(200, { ok: true, geaendert }, setCookies);
    }

    if (eintrag.aktion === "ort_bearbeiten") {
      const { data: aktuell } = await db.from("orte").select(`id, typ, ${STAMMDATEN_FELDER.join(", ")}`).eq("id", ziel).maybeSingle();
      const plan = rueckgaengigPlan(eintrag, aktuell as unknown as Record<string, unknown> | null);
      if (!plan.ok) return adminAntwort(409, { fehler: plan.fehler }, setCookies);
      const typ = String((aktuell as unknown as { typ?: unknown }).typ ?? "");
      const pruefung = stammdatenPruefen(plan.felder, typ);
      if (!pruefung.ok) return adminAntwort(400, { fehler: `Rückgängig nicht möglich: ${pruefung.fehler}` }, setCookies);
      const update = aenderungen(aktuell as unknown as Record<string, unknown>, pruefung.felder);
      if (!Object.keys(update).length) return adminAntwort(200, { ok: true, geaendert: [] }, setCookies);
      let q = db.from("orte").update(update).eq("id", ziel);
      for (const [f, w] of plan.erwartet) q = w === null ? q.is(f, null) : q.eq(f, w as string | number | boolean);
      const { data: neu, error: f2 } = await q.select("id");
      if (f2) return adminAntwort(400, { fehler: f2.message }, setCookies);
      if (!neu?.length) return adminAntwort(409, { fehler: "Gerade eben anders geändert oder keine Schreibrechte – bitte neu laden." }, setCookies);
      await protokollieren(db, { aktion: "ort_rueckgaengig", tabelle: "orte", ziel_id: ziel, vorher: eintrag.nachher, nachher: { ...update, protokoll: id } });
      revalidateTag(ORTE_CACHE_TAG, { expire: 0 });
      orteZwischenspeicherVerwerfen();
      return adminAntwort(200, { ok: true, geaendert: Object.keys(update) }, setCookies);
    }

    return adminAntwort(400, { fehler: "Diese Aktion lässt sich nicht automatisch rückgängig machen." }, setCookies);
  });
}
