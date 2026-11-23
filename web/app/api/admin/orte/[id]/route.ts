// Admin-Bereich – ein Ort lesen und bearbeiten (Plan Admin-Dashboard 4.7, Stufe 3a).
// GET                                                  → Ort, Säle, Weiterleitungen, kommende Events
// POST { felder }                                      → Stammdaten (Whitelist, UPDATE über Policy orte_admin_aendern)
// POST { aktion: "score", score, grund }               → admin_ort_score_setzen
// POST { aktion: "text", text, quellen, freigeben }    → admin_ort_text_speichern (nur Spielstätten)
// POST { aktion: "schliessen", ziel, grund, loeschen } → admin_ort_schliessen (mit Weiterleitung)
// POST { aktion: "zusammenlegen", nach, grund }        → admin_ort_zusammenlegen (dieser Ort geht in „nach“ auf)
// POST { aktion: "zuordnung_loesen", event }           → admin_ort_zuordnung_loesen
// GET ?vergangene=1 → statt der kommenden die letzten 100 Events (auch alte Zuordnungen lösen, Cursor 3a Befund 4)
// Stufe 3b (database/admin_guides_2026-11-23.sql):
// POST { aktion: "bild", bild: {art, google_foto?, bild_url?, bild_attribution?, bild_link?} } → admin_ort_bild_setzen
// POST { aktion: "bild_fokus", fokus }                → admin_ort_bild_fokus
// POST { aktion: "club", club, grund? }               → admin_club_setzen (freigeben, freigabe_entziehen, aus_hub, in_hub)
// POST { aktion: "wm", wm, wert? }                    → admin_wm_setzen (rang, ausschliessen, einschliessen, freischalten)
// POST { aktion: "spielplatz", spielplatz, wert? }    → admin_spielplatz_setzen (bestaetigen, …, freischalten)
import { revalidateTag } from "next/cache";
import { aenderungen, oeffentlicherPfad, ortKopf, stammdatenPruefen, STAMMDATEN_FELDER, textPruefen } from "@/lib/admin/orte";
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { EVENTS_CACHE_TAG } from "@/lib/daten";
import { heuteBerlin } from "@/lib/datum";
import { ORTE_CACHE_TAG } from "@/lib/orte";
import { orteZwischenspeicherVerwerfen } from "@/lib/pfad-pruefung";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SPALTEN =
  "id, name, slug, typ, untertitel, beschreibung, highlight, adresse, stadtteil, latitude, longitude, bild_url, " +
  "bild_attribution, preis_niveau, oeffnungszeiten, webseite, telefon, instagram, google_place_id, google_rating, " +
  "qualitaets_score, sortierung, aktiv, parent_id, erstellt_am, aktualisiert_am, " +
  "spielstaette:extras->spielstaette, club:extras->club, club_score:extras->club_score, " +
  "club_freigegeben:extras->club_freigegeben, auch_club:extras->auch_club, kein_club:extras->kein_club, " +
  "score_manuell:extras->score_manuell, google_foto:extras->google_foto, bild_fokus:extras->bild_fokus, " +
  "bild_link:extras->bild_link, foto_manuell:extras->foto_manuell, foto_version:extras->foto_version, " +
  "unterart:extras->unterart, vorher_typ:extras->vorher_typ, weihnachtsmarkt:extras->weihnachtsmarkt, " +
  "spielplatz:extras->spielplatz";

const CLUB_AKTIONEN = ["freigeben", "freigabe_entziehen", "aus_hub", "in_hub"];
const WM_AKTIONEN = ["rang", "ausschliessen", "einschliessen", "freischalten"];
const SPIELPLATZ_AKTIONEN = ["bestaetigen", "bestaetigung_entziehen", "ausschliessen", "einschliessen", "freischalten"];

type OrtZeile = Record<string, unknown> & { id: string; slug: string; typ: string; aktiv: boolean | null; qualitaets_score: number | null; stadtteil: string | null };

function cacheLeeren(events: boolean) {
  revalidateTag(ORTE_CACHE_TAG, { expire: 0 });
  // Der Proxy merkt sich /orte- und Guide-Entscheidungen bis zu 10 Minuten (Cursor-Prüfung 3a, Befund 1)
  orteZwischenspeicherVerwerfen();
  if (events) revalidateTag(EVENTS_CACHE_TAG, { expire: 0 });
}

function kopfAus(z: OrtZeile) {
  return ortKopf({
    typ: z.typ,
    aktiv: z.aktiv,
    qualitaets_score: z.qualitaets_score,
    stadtteil: z.stadtteil,
    extras_kopf: { club: z.club, club_score: z.club_score, club_freigegeben: z.club_freigegeben, auch_club: z.auch_club, kein_club: z.kein_club },
  });
}

export async function GET(request: Request, ctx: RouteContext<"/api/admin/orte/[id]">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const db = admin!.db;
    const { data, error } = await db.from("orte").select(SPALTEN).eq("id", id).maybeSingle();
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    if (!data) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const ort = data as unknown as OrtZeile;
    const heute = heuteBerlin(new Date());
    const vergangene = new URL(request.url).searchParams.get("vergangene") === "1";
    const eventAbfrage = db
      .from("events")
      .select("id, titel, datum, datum_bis, uhrzeit, ort, abgelehnt, abgesagt, quelle_name", { count: "exact" })
      .eq("ort_id", id);
    const [haus, saele, weiterAufMich, eigeneWeiter, events] = await Promise.all([
      ort.parent_id ? db.from("orte").select("id, name, slug, aktiv").eq("id", String(ort.parent_id)).maybeSingle() : Promise.resolve({ data: null }),
      db.from("orte").select("id, name, slug, aktiv").eq("parent_id", id).order("name"),
      db.from("ort_weiterleitungen").select("alter_slug, grund, erstellt_am").eq("ziel_ort_id", id).order("alter_slug"),
      db.from("ort_weiterleitungen").select("alter_slug, ziel_ort_id, grund").eq("alter_slug", ort.slug).maybeSingle(),
      vergangene
        ? eventAbfrage.order("datum", { ascending: false }).limit(100)
        : eventAbfrage.or(`datum.gte.${heute},datum_bis.gte.${heute}`).order("datum").limit(60),
    ]);
    return adminAntwort(
      200,
      {
        ort,
        pfad: oeffentlicherPfad(ort.slug, kopfAus(ort)),
        haus: haus.data ?? null,
        saele: saele.data ?? [],
        weiterleitungen: weiterAufMich.data ?? [],
        eigeneWeiterleitung: eigeneWeiter.data ?? null,
        events: events.data ?? [],
        eventsGesamt: events.count ?? 0,
        vergangene,
      },
      setCookies,
    );
  });
}

export async function POST(request: Request, ctx: RouteContext<"/api/admin/orte/[id]">) {
  const { id } = await ctx.params;
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    if (!UUID.test(id)) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const db = admin!.db;
    const fehler = (e: { message: string }) => adminAntwort(400, { fehler: e.message, code: "db" }, setCookies);
    const { data: bisherDaten, error: f1 } = await db.from("orte").select(`id, slug, typ, ${STAMMDATEN_FELDER.join(", ")}`).eq("id", id).maybeSingle();
    if (f1) return adminAntwort(500, { fehler: f1.message, code: "db" }, setCookies);
    if (!bisherDaten) return adminAntwort(404, { fehler: "Nicht gefunden." }, setCookies);
    const bisher = bisherDaten as unknown as Record<string, unknown> & { typ: string; slug: string };
    const grund = typeof body.grund === "string" ? body.grund.trim() : "";

    if (body.aktion === "score") {
      const score = body.score === null || body.score === "" ? null : Number(body.score);
      if (score !== null && (!Number.isInteger(score) || score < 1 || score > 10)) return adminAntwort(400, { fehler: "Score 1 bis 10 oder leer.", code: "eingabe" }, setCookies);
      const { error } = await db.rpc("admin_ort_score_setzen", { p_id: id, p_score: score, p_grund: grund || null });
      if (error) return fehler(error);
      cacheLeeren(false);
      return adminAntwort(200, { ok: true }, setCookies);
    }

    if (body.aktion === "text") {
      const freigeben = body.freigeben === true;
      const t = textPruefen(body.text, body.quellen, freigeben);
      if (!t.ok) return adminAntwort(400, { fehler: t.fehler, code: "eingabe" }, setCookies);
      const { error } = await db.rpc("admin_ort_text_speichern", { p_id: id, p_text: t.text, p_quellen: t.quellen, p_freigeben: freigeben });
      if (error) return fehler(error);
      if (freigeben) cacheLeeren(false);
      return adminAntwort(200, { ok: true, freigegeben: freigeben }, setCookies);
    }

    if (body.aktion === "schliessen") {
      const ziel = typeof body.ziel === "string" && body.ziel ? body.ziel : null;
      if (ziel && !UUID.test(ziel)) return adminAntwort(400, { fehler: "Ungültiges Ziel.", code: "eingabe" }, setCookies);
      if (grund.length < 3) return adminAntwort(400, { fehler: "Bitte einen Grund angeben.", code: "eingabe" }, setCookies);
      const loeschen = body.loeschen === true;
      // Spielplätze und Weihnachtsmärkte leiten nur als abgeschaltete Zeile (mit freigeschaltet_am) auf ihren Hub
      // weiter; gelöscht endete /guides/… als 404 (Cursor-Prüfung 3a, Befund 2). Löschen erst mit der Guide-Pflege (3b).
      if (loeschen && (bisher.typ === "spielplatz" || bisher.typ === "weihnachtsmarkt")) {
        return adminAntwort(400, { fehler: "Spielplätze und Weihnachtsmärkte bitte nur schließen, nicht löschen.", code: "eingabe" }, setCookies);
      }
      const { data, error } = await db.rpc("admin_ort_schliessen", { p_id: id, p_ziel: ziel, p_grund: grund, p_loeschen: loeschen });
      if (error) return fehler(error);
      cacheLeeren(true);
      return adminAntwort(200, { ok: true, ergebnis: data, weiter: loeschen ? "/admin/orte" : null }, setCookies);
    }

    if (body.aktion === "zusammenlegen") {
      const nach = typeof body.nach === "string" ? body.nach : "";
      if (!UUID.test(nach) || nach === id) return adminAntwort(400, { fehler: "Ungültiger Ziel-Ort.", code: "eingabe" }, setCookies);
      if (grund.length < 3) return adminAntwort(400, { fehler: "Bitte einen Grund angeben.", code: "eingabe" }, setCookies);
      const { data, error } = await db.rpc("admin_ort_zusammenlegen", { p_von: id, p_nach: nach, p_grund: grund });
      if (error) return fehler(error);
      cacheLeeren(true);
      return adminAntwort(200, { ok: true, ergebnis: data, weiter: `/admin/orte/${nach}` }, setCookies);
    }

    if (body.aktion === "zuordnung_loesen") {
      const event = typeof body.event === "string" ? body.event : "";
      if (!UUID.test(event)) return adminAntwort(400, { fehler: "Ungültiges Event.", code: "eingabe" }, setCookies);
      const { error } = await db.rpc("admin_ort_zuordnung_loesen", { p_event: event, p_ort: id });
      if (error) return fehler(error);
      cacheLeeren(true);
      return adminAntwort(200, { ok: true }, setCookies);
    }

    // ---------- Stufe 3b: Bilder ----------
    if (body.aktion === "bild" || body.aktion === "bild_fokus") {
      const { error } =
        body.aktion === "bild"
          ? await db.rpc("admin_ort_bild_setzen", { p_id: id, p_bild: body.bild && typeof body.bild === "object" ? body.bild : {} })
          : await db.rpc("admin_ort_bild_fokus", { p_id: id, p_fokus: typeof body.fokus === "string" ? body.fokus : null });
      if (error) return fehler(error);
      cacheLeeren(false);
      // /ort-foto/<slug> merkt sich die Google-Bildadresse 30 Tage (app/ort-foto/[slug]/route.ts, fotoTag)
      if (body.aktion === "bild") revalidateTag(`ort-foto:${bisher.slug}`.slice(0, 256), { expire: 0 });
      return adminAntwort(200, { ok: true }, setCookies);
    }

    // ---------- Stufe 3b: Guide-Pflege ----------
    if (body.aktion === "club" || body.aktion === "wm" || body.aktion === "spielplatz") {
      const art = body.aktion;
      const schritt = String(body[art] ?? "");
      const erlaubt = art === "club" ? CLUB_AKTIONEN : art === "wm" ? WM_AKTIONEN : SPIELPLATZ_AKTIONEN;
      if (!erlaubt.includes(schritt)) return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);
      const wert = typeof body.wert === "string" || typeof body.wert === "number" ? String(body.wert) : null;
      const { data, error } =
        art === "club"
          ? await db.rpc("admin_club_setzen", { p_id: id, p_aktion: schritt, p_grund: grund || null })
          : await db.rpc(art === "wm" ? "admin_wm_setzen" : "admin_spielplatz_setzen", { p_id: id, p_aktion: schritt, p_wert: wert });
      if (error) return fehler(error);
      cacheLeeren(false);
      return adminAntwort(200, { ok: true, ergebnis: data }, setCookies);
    }

    if (body.aktion !== undefined) return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);

    // Stammdaten
    const eingabe = body.felder && typeof body.felder === "object" && !Array.isArray(body.felder) ? (body.felder as Record<string, unknown>) : {};
    const pruefung = stammdatenPruefen(eingabe, bisher.typ);
    if (!pruefung.ok) return adminAntwort(400, { fehler: pruefung.fehler, code: "eingabe" }, setCookies);
    const update = aenderungen(bisher, pruefung.felder);
    const geaendert = Object.keys(update);
    if (!geaendert.length) return adminAntwort(200, { ok: true, geaendert: [] }, setCookies);
    // .select() → 0 Zeilen heißt: die Policy hat das UPDATE nicht erlaubt (statt stillem Erfolg)
    const { data: neu, error } = await db.from("orte").update(update).eq("id", id).select("id");
    if (error) return fehler(error);
    if (!neu?.length) return adminAntwort(403, { fehler: "Keine Schreibrechte auf Orte – SQL admin_orte_2026-11-23.sql ausgeführt?", code: "rechte" }, setCookies);
    await protokollieren(db, { aktion: "ort_bearbeiten", tabelle: "orte", ziel_id: id, vorher: Object.fromEntries(geaendert.map((k) => [k, bisher[k] ?? null])), nachher: update });
    cacheLeeren(false);
    return adminAntwort(200, { ok: true, geaendert }, setCookies);
  });
}
