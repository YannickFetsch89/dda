// Admin-Bereich – Event-Meldungen von der Website (Plan Admin-Dashboard 4.10, Stufe 5b; Umzug aus
// dashboard/meldungen.py, gleicher Ablauf). Alles mit dem Token des Admins (RLS und Storage-Policies aus
// database/meldungen_newsletter_2026-11-05.sql: Meldungen lesen/ändern, Events anlegen, Bilder lesen/kopieren/löschen).
// GET                                         → offene Meldungen (älteste zuerst, mit Bild-Link für 1 h) und zuletzt bearbeitete
// POST { aktion: "freigeben", id, werte }     → reservieren → Bild veröffentlichen → Event anlegen → abschließen
//                                               (mail_status „offen“) → Mail-Job starten (database/meldung_mail_2026-11-24.sql)
// POST { aktion: "ablehnen", id, grund }      → reservieren → abschließen → privates Bild löschen
import { revalidateTag } from "next/cache";
import type { SupabaseClient } from "@supabase/supabase-js";
import { workflowStarten } from "@/lib/admin/github";
import { freigabePruefen, kuerzen, slugErzeugen, slugMitSuffix, stadtteilAusAdresse, type FreigabeWerte } from "@/lib/admin/meldungen";
import { protokollieren } from "@/lib/admin/protokoll";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { EVENTS_CACHE_TAG } from "@/lib/daten";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SPERRE_MINUTEN = 10; // so lange gilt eine angefangene Bearbeitung als „in Arbeit“ (wie im Dashboard)
const QUELLE_NAME = "Event-Meldung";
const QUELLE_STANDARD_URL = "https://diesdas.events/event-melden";

class FreigabeFehler extends Error {}

type Meldung = Record<string, unknown> & { id: string; bild_pfad: string | null; bild_rechte: boolean };

async function reservieren(db: SupabaseClient, id: string, adminId: string): Promise<string> {
  const grenze = new Date(Date.now() - SPERRE_MINUTEN * 60_000).toISOString();
  const { data, error } = await db
    .from("event_meldungen")
    .update({ bearbeitet_am: new Date().toISOString(), bearbeitet_von: adminId })
    .eq("id", id)
    .eq("status", "neu")
    .or(`bearbeitet_am.is.null,bearbeitet_am.lt.${grenze}`)
    .select("bearbeitet_am");
  if (error) throw new Error(error.message);
  if (!data?.length) throw new FreigabeFehler("Diese Meldung wird gerade bearbeitet oder ist schon erledigt – bitte neu laden.");
  return String(data[0].bearbeitet_am);
}

async function abschliessen(db: SupabaseClient, id: string, token: string, adminId: string, werte: Record<string, unknown>): Promise<boolean> {
  const { data, error } = await db
    .from("event_meldungen")
    .update({ ...werte, bearbeitet_am: new Date().toISOString(), bearbeitet_von: adminId })
    .eq("id", id)
    .eq("status", "neu")
    .eq("bearbeitet_am", token)
    .select("id");
  if (error) throw new Error(error.message);
  return !!data?.length;
}

async function reservierungLoesen(db: SupabaseClient, id: string, token: string) {
  await db.from("event_meldungen").update({ bearbeitet_am: null, bearbeitet_von: null }).eq("id", id).eq("status", "neu").eq("bearbeitet_am", token);
}

/** Bild aus dem privaten in den öffentlichen Bucket kopieren (eigener Pfad je Versuch) → [URL, Pfad] oder [null, null] */
async function bildVeroeffentlichen(db: SupabaseClient, m: Meldung): Promise<[string | null, string | null]> {
  if (!m.bild_pfad || !m.bild_rechte) return [null, null];
  const endung = m.bild_pfad.split(".").pop()?.toLowerCase() ?? "jpg";
  const typ = { jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", webp: "image/webp" }[endung] ?? "image/jpeg";
  const { data: datei, error } = await db.storage.from("event-meldungen").download(m.bild_pfad);
  if (error || !datei) throw new Error(`Bild nicht lesbar: ${error?.message ?? "leer"}`);
  const ziel = `meldungen/${m.id}-${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}.${endung}`;
  const { error: f2 } = await db.storage.from("event-bilder").upload(ziel, datei, { contentType: typ, upsert: false });
  if (f2) throw new Error(`Bild nicht hochgeladen: ${f2.message}`);
  return [db.storage.from("event-bilder").getPublicUrl(ziel).data.publicUrl, ziel];
}

/** Event anlegen; bei Slug-Kollision einmal mit neuem Slug wiederholen (wie _event_einfuegen) */
async function eventEinfuegen(db: SupabaseClient, event: Record<string, unknown>): Promise<string> {
  for (let versuch = 0; versuch < 2; versuch++) {
    const basis = slugErzeugen(String(event.titel), String(event.ort ?? ""), String(event.datum));
    // Platzhalter * wie im früheren Streamlit-Dashboard. Live geprüft 24.11.2026: % und * liefern über supabase-js dieselben
    // Treffer (Cursor-Prüfung 5b, Befund 1, war ein Fehlalarm). Slugs enthalten nur a-z, 0-9 und „-“.
    const { data: belegt, error: fBelegt } = await db.from("events").select("slug").like("slug", `${basis}*`);
    if (fBelegt) throw new Error(fBelegt.message);
    event.slug = slugMitSuffix(basis, new Set((belegt ?? []).map((z) => String(z.slug))));
    const { data, error } = await db.from("events").insert(event).select("id");
    if (!error && data?.length) return String(data[0].id);
    if (error?.code === "23505" && error.message.includes("slug") && versuch === 0) continue;
    if (error?.code === "23505") throw new FreigabeFehler("Ein Event mit gleichem Titel, Datum, Ort und Uhrzeit gibt es schon (ggf. ausgeblendet).");
    throw new Error(error?.message ?? "Event nicht angelegt.");
  }
  throw new FreigabeFehler("Slug konnte nicht vergeben werden – bitte erneut versuchen.");
}

async function freigeben(db: SupabaseClient, m: Meldung, w: FreigabeWerte, adminId: string): Promise<string> {
  const token = await reservieren(db, m.id, adminId);
  let bildZiel: string | null = null;
  let eventId: string | null = null;
  try {
    const [bildUrl, ziel] = await bildVeroeffentlichen(db, m);
    bildZiel = ziel;
    eventId = await eventEinfuegen(db, {
      titel: w.titel,
      datum: w.datum,
      datum_bis: w.datum_bis,
      uhrzeit: w.uhrzeit,
      ort: w.ort,
      adresse: w.adresse,
      stadtteil: w.stadtteil ?? stadtteilAusAdresse(w.adresse),
      kategorie: w.kategorie,
      beschreibung: kuerzen(w.beschreibung),
      preis: w.preis,
      quelle_name: QUELLE_NAME,
      quelle_url: w.link ?? QUELLE_STANDARD_URL,
      bild_url: bildUrl,
      bild_generiert: false,
      post_typ: "feed",
      status: "neu",
    });
    if (!(await abschliessen(db, m.id, token, adminId, { status: "freigegeben", event_id: eventId, mail_status: "offen" }))) {
      throw new FreigabeFehler("Die Reservierung ist abgelaufen oder die Meldung wurde inzwischen anders bearbeitet – Freigabe zurückgenommen.");
    }
  } catch (e) {
    // Rückabwicklung: Löschen dürfen Admins Events nicht → das neue Event wird ausgeblendet
    let bildFrei = true;
    if (eventId) {
      const { error } = await db.from("events").update({ abgelehnt: true, bild_url: null }).eq("id", eventId);
      if (error) {
        bildFrei = false;
        console.error(`Meldung: Event ${eventId} nach Fehler nicht ausgeblendet – bitte prüfen`);
      }
    }
    if (bildZiel && bildFrei) await db.storage.from("event-bilder").remove([bildZiel]);
    await reservierungLoesen(db, m.id, token);
    throw e;
  }
  // Privates Original wird nicht mehr gebraucht
  if (m.bild_pfad) await db.storage.from("event-meldungen").remove([m.bild_pfad]);
  return eventId;
}

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const db = admin!.db;
    const [offen, erledigt] = await Promise.all([
      db.from("event_meldungen").select("*").eq("status", "neu").order("erstellt_am").limit(100),
      db.from("event_meldungen").select("id, titel, datum, status, bearbeitet_am, ablehngrund, event_id, mail_status, mail_gesendet_am").neq("status", "neu").order("bearbeitet_am", { ascending: false }).limit(30),
    ]);
    if (offen.error) return adminAntwort(500, { fehler: offen.error.message, code: "db" }, setCookies);
    const liste = await Promise.all(
      (offen.data ?? []).map(async (m) => {
        let bild: string | null = null;
        if (m.bild_pfad) {
          const { data } = await db.storage.from("event-meldungen").createSignedUrl(String(m.bild_pfad), 3600);
          bild = data?.signedUrl ?? null;
        }
        return { ...m, bild_link: bild, stadtteil_vorschlag: stadtteilAusAdresse(m.adresse as string | null) };
      }),
    );
    return adminAntwort(200, { offen: liste, erledigt: erledigt.data ?? [] }, setCookies);
  });
}

export async function POST(request: Request) {
  return adminRoute(request, {}, async ({ admin, body, setCookies }) => {
    const id = typeof body.id === "string" ? body.id : "";
    if (!UUID.test(id)) return adminAntwort(400, { fehler: "Ungültige Meldung." }, setCookies);
    const db = admin!.db;
    const adminId = admin!.sitzung.nutzerId;
    const { data: m, error } = await db.from("event_meldungen").select("*").eq("id", id).maybeSingle();
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    if (!m) return adminAntwort(404, { fehler: "Meldung nicht gefunden." }, setCookies);
    try {
      if (body.aktion === "freigeben") {
        const p = freigabePruefen(body.werte && typeof body.werte === "object" ? (body.werte as Record<string, unknown>) : {});
        if (!p.ok) return adminAntwort(400, { fehler: p.fehler, code: "eingabe" }, setCookies);
        const eventId = await freigeben(db, m as Meldung, p.werte, adminId);
        await protokollieren(db, { aktion: "meldung_freigeben", tabelle: "event_meldungen", ziel_id: id, nachher: { event_id: eventId } });
        revalidateTag(EVENTS_CACHE_TAG, { expire: 0 });
        // Bestätigungsmail an den Melder sofort anstoßen (sonst nimmt der stündliche Lauf sie mit). Der Job prüft den
        // Schalter MELDUNG_MAIL_AKTIV selbst; ein Fehler hier hält die Freigabe nicht auf.
        const start = await workflowStarten("meldung-mail", { aufgabe: "senden" });
        if (!start.ok) console.error(`Meldung: Mail-Job nicht gestartet (${start.meldung}) – der stündliche Lauf holt sie nach`);
        return adminAntwort(200, { ok: true, event_id: eventId, mail_job: start.ok }, setCookies);
      }
      if (body.aktion === "ablehnen") {
        const grund = typeof body.grund === "string" ? body.grund.trim().slice(0, 300) : "";
        const token = await reservieren(db, id, adminId);
        let erledigt = false;
        try {
          erledigt = await abschliessen(db, id, token, adminId, { status: "abgelehnt", ablehngrund: grund || null });
        } catch (e) {
          await reservierungLoesen(db, id, token);
          throw e;
        }
        if (!erledigt) throw new FreigabeFehler("Diese Meldung wurde inzwischen anders bearbeitet – bitte neu laden.");
        let warnung: string | null = null;
        if (m.bild_pfad) {
          const { error: f } = await db.storage.from("event-meldungen").remove([String(m.bild_pfad)]);
          if (f) warnung = `Abgelehnt, aber das Bild konnte nicht gelöscht werden (${m.bild_pfad}) – bitte im Supabase-Storage entfernen.`;
        }
        await protokollieren(db, { aktion: "meldung_ablehnen", tabelle: "event_meldungen", ziel_id: id, nachher: { grund } });
        return adminAntwort(200, { ok: true, warnung }, setCookies);
      }
      return adminAntwort(400, { fehler: "Unbekannte Aktion." }, setCookies);
    } catch (e) {
      if (e instanceof FreigabeFehler) return adminAntwort(409, { fehler: e.message }, setCookies);
      return adminAntwort(500, { fehler: e instanceof Error ? e.message : "Hat nicht geklappt." }, setCookies);
    }
  });
}
