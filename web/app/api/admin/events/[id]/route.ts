// Admin-Bereich – ein Event lesen und bearbeiten (Plan Admin-Dashboard 4.4).
// POST { felder }                      → Felder ändern (Whitelist, Feldschutz, abgleich_* beim ersten Mal)
// POST { aktion: "zuruecksetzen" }     → redaktion_felder und abgleich_* leeren (Pipeline darf wieder schreiben)
// POST { aktion: "dublette", behalten } → dieses Event ist Dublette von „behalten“ (admin_dublette_zusammenlegen)
import { revalidateTag } from "next/cache";
import { eingabenPruefen, uhrzeitUebernehmen, updateBauen, type EventZeile } from "@/lib/admin/events";
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { EVENTS_CACHE_TAG } from "@/lib/daten";
import { kategorieAusDb } from "@/lib/kategorien";
import { eventPfad } from "@/lib/pfade";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SPALTEN =
  "id, slug, titel, datum, datum_bis, uhrzeit, ort, adresse, stadtteil, kategorie, unterkategorie, preis, beschreibung, " +
  "bild_url, ort_id, quelle_name, quelle_url, abgelehnt, abgesagt, nicht_empfehlen, tipp_des_tages, highlight_der_woche, " +
  "top_event_des_monats, erstellt_am, redaktion_felder, abgleich_titel, abgleich_datum, abgleich_uhrzeit, abgleich_ort";

function cacheLeeren(id: string, bild: boolean) {
  revalidateTag(EVENTS_CACHE_TAG, { expire: 0 });
  if (bild) revalidateTag(`event-bild-${id}`, { expire: 0 });
}

export async function GET(request: Request, ctx: RouteContext<"/api/admin/events/[id]">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const { data, error } = await admin!.db.from("events").select(SPALTEN).eq("id", id).maybeSingle();
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    if (!data) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const e = data as unknown as EventZeile & { slug: string | null; kategorie: string };
    return adminAntwort(200, { event: e, pfad: eventPfad({ id: e.id, slug: e.slug, kategorie: kategorieAusDb(e.kategorie) }) }, setCookies);
  });
}

export async function POST(request: Request, ctx: RouteContext<"/api/admin/events/[id]">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const db = admin!.db;
    const { data: bisherDaten, error: f1 } = await db.from("events").select(SPALTEN).eq("id", id).maybeSingle();
    if (f1) return adminAntwort(500, { fehler: f1.message, code: "db" }, setCookies);
    if (!bisherDaten) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const bisher = bisherDaten as unknown as EventZeile;

    // Redaktionsänderungen zurücksetzen
    if (body.aktion === "zuruecksetzen") {
      const update = { redaktion_felder: [], abgleich_titel: null, abgleich_datum: null, abgleich_uhrzeit: null, abgleich_ort: null };
      const { error } = await db.from("events").update(update).eq("id", id);
      if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
      await protokollieren(db, { aktion: "event_zuruecksetzen", tabelle: "events", ziel_id: id, vorher: { redaktion_felder: bisher.redaktion_felder, abgleich_datum: bisher.abgleich_datum }, nachher: update });
      cacheLeeren(id, false);
      return adminAntwort(200, { ok: true }, setCookies);
    }

    // Als Dublette eines anderen Events markieren
    if (body.aktion === "dublette") {
      const behalten = typeof body.behalten === "string" ? body.behalten : "";
      if (!UUID.test(behalten) || behalten === id) return adminAntwort(400, { fehler: "Ungültiges Ziel-Event." }, setCookies);
      const { data: ziel } = await db.from("events").select("id, slug, kategorie, uhrzeit, quelle_name, quelle_url").eq("id", behalten).maybeSingle();
      if (!ziel?.slug) return adminAntwort(400, { fehler: "Ziel-Event hat keine Seite (kein Slug)." }, setCookies);
      const { data, error } = await db.rpc("admin_dublette_zusammenlegen", {
        p_behalten: behalten,
        p_dublette: id,
        p_ziel: eventPfad({ id: ziel.id, slug: ziel.slug, kategorie: kategorieAusDb(ziel.kategorie) }),
        // Gleiche Regel wie der Vorschlagsweg (pipeline/vorschlaege.py): Veranstalter-Uhrzeit schlägt Sammel-Quelle.
        // Die Absage der Dublette übernimmt die Funktion selbst (d.abgesagt).
        p_uhrzeit_uebernehmen: uhrzeitUebernehmen(ziel, bisher),
        p_absage: false,
      });
      if (error) return adminAntwort(400, { fehler: error.message, code: "db" }, setCookies);
      cacheLeeren(behalten, true);
      return adminAntwort(200, { ok: true, ergebnis: data, weiter: `/admin/events/${behalten}` }, setCookies);
    }

    // Felder ändern
    const eingabe = body.felder && typeof body.felder === "object" && !Array.isArray(body.felder) ? (body.felder as Record<string, unknown>) : {};
    const pruefung = eingabenPruefen(eingabe);
    if (!pruefung.ok) return adminAntwort(400, { fehler: pruefung.fehler, code: "eingabe" }, setCookies);
    const { update, geaendert } = updateBauen(bisher, pruefung.felder);
    if (!geaendert.length) return adminAntwort(200, { ok: true, geaendert: [] }, setCookies);

    const { error } = await db.from("events").update(update).eq("id", id);
    if (error) {
      if (error.code === "23505") {
        return adminAntwort(409, { fehler: "Ein Event mit diesem Titel, Datum, Ort und dieser Uhrzeit gibt es schon. Bitte als Dublette zusammenlegen.", code: "doppelt" }, setCookies);
      }
      return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    }
    const vorher = Object.fromEntries(geaendert.map((f) => [f, bisher[f] ?? null]));
    await protokollieren(db, { aktion: "event_bearbeiten", tabelle: "events", ziel_id: id, vorher, nachher: update });
    cacheLeeren(id, geaendert.includes("bild_url"));
    return adminAntwort(200, { ok: true, geaendert }, setCookies);
  });
}
