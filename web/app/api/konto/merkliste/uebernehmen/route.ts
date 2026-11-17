// Übernahme der lokalen Merkliste ins Konto (Plan 5.4 Schritte 4–7, 5.8). Fügt nur ein, löscht nie.
// Existenz, Ablehnung und Weiterleitung prüft der Dienst-Client (abgelehnte Events sieht der Nutzer-Client wegen
// RLS nicht). Welche Events nur auf dem Gerät bleiben dürfen, steht nur in der Antwort (bleiben_auf_geraet),
// nie mit Grund.
import { kontoDienstClient } from "@/lib/konto/clients";
import { MELDUNG, MERKLISTE_MAX, UEBERNAHME_MAX_BYTES } from "@/lib/konto/konfig";
import { dbFehlercode, kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";
import { slugAusEventPfad, uebernahmeVorbereiten, zuVieleIds, type EventStand } from "@/lib/konto/uebernahme";
import { uuidGueltig } from "@/lib/konto/pruefungen";

export const POST = kontoRoute(
  {
    anmeldung: true, json: true, aendernd: true, maxBytes: UEBERNAHME_MAX_BYTES,
    limit: { name: "uebernehmen", max: 10, fensterMs: ZEIT.STUNDE },
  },
  async (ctx) => {
    const ids = ctx.body.ids;
    if (!Array.isArray(ids)) return kontoAntwort(400, { fehler: MELDUNG.ungueltig });
    if (zuVieleIds(ids)) return kontoAntwort(413, { fehler: "Zu viele Einträge auf diesem Gerät.", code: "zu_viele_ids" });
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const nutzerId = ctx.sitzung!.nutzerId;
    const db = ctx.db!;

    // Stand der Events (Existenz, abgelehnt, Weiterleitung)
    const uuids = [...new Set(ids.filter(uuidGueltig).map((i) => i.toLowerCase()))];
    const stand = new Map<string, EventStand>();
    const weiterleitungen = new Map<string, string>(); // abgelehnte ID → Slug des Ziels
    for (let i = 0; i < uuids.length; i += 200) {
      const teil = uuids.slice(i, i + 200);
      const { data, error } = await dienst.from("events").select("id, abgelehnt").in("id", teil);
      if (error) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
      for (const e of data ?? []) stand.set(e.id, { vorhanden: true, abgelehnt: !!e.abgelehnt, weiterleitungAuf: null });
      const abgelehnt = (data ?? []).filter((e) => e.abgelehnt).map((e) => e.id as string);
      if (abgelehnt.length) {
        const { data: seo } = await dienst
          .from("event_seo_entscheidungen")
          .select("event_id, aktion, ziel")
          .in("event_id", abgelehnt)
          .eq("aktion", "weiterleiten");
        for (const s of seo ?? []) {
          const slug = slugAusEventPfad(s.ziel as string);
          if (slug) weiterleitungen.set(s.event_id as string, slug);
        }
      }
    }
    if (weiterleitungen.size) {
      const { data: ziele } = await dienst
        .from("events")
        .select("id, slug")
        .in("slug", [...new Set(weiterleitungen.values())])
        .eq("abgelehnt", false);
      const idZuSlug = new Map((ziele ?? []).map((z) => [z.slug as string, z.id as string]));
      for (const [von, slug] of weiterleitungen) {
        const nach = idZuSlug.get(slug);
        const s = stand.get(von);
        if (s && nach) s.weiterleitungAuf = nach;
      }
    }

    const vorb = uebernahmeVorbereiten(ids, stand);

    // Was liegt schon im Konto? (eigene Zeilen, RLS)
    const { data: konto0, error: kontoFehler } = await db.from("merkliste").select("event_id");
    if (kontoFehler) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const imKonto = new Set((konto0 ?? []).map((z) => z.event_id as string));

    // Ohne Einwilligung (b): sensible Events bleiben auf dem Gerät (Plan 5.8). Die Liste verlässt den Server nur
    // als neutrale ID-Liste.
    let nurGeraet = new Set<string>();
    if (!ctx.profil!.sensible_events_erlaubt && vorb.kandidaten.length) {
      const { data: sens, error } = await dienst.from("event_sensibel").select("event_id").in("event_id", vorb.kandidaten);
      if (error) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
      nurGeraet = new Set((sens ?? []).map((z) => z.event_id as string));
    }

    const neu = vorb.kandidaten.filter((id) => !imKonto.has(id) && !nurGeraet.has(id));
    const frei = Math.max(0, MERKLISTE_MAX - imKonto.size);
    const einfuegen = neu.slice(0, frei);
    const nichtUebernommen = neu.slice(frei);

    if (einfuegen.length) {
      const { error } = await db
        .from("merkliste")
        .upsert(einfuegen.map((event_id) => ({ nutzer_id: nutzerId, event_id, quelle: "geraet" })), {
          onConflict: "nutzer_id,event_id",
          ignoreDuplicates: true,
        });
      if (error) {
        const code = dbFehlercode(error);
        // Gleichzeitig von einem anderen Gerät gefüllt oder neu gekennzeichnet: nichts geschrieben (eine Anweisung),
        // die Geräteliste bleibt unverändert, der nächste Versuch beginnt neu (Plan 5.4 Schritt 10)
        console.error(`Übernahme fehlgeschlagen (${code ?? error.code})`);
        return kontoAntwort(code === "mindestalter_fehlt" ? 403 : 409, { fehler: "Übernahme nicht möglich, bitte nochmal versuchen.", code: code ?? "fehler" });
      }
    }

    const { data: konto1 } = await db.from("merkliste").select("event_id").order("gemerkt_am", { ascending: false });
    return kontoAntwort(200, {
      ok: true,
      konto: (konto1 ?? []).map((z) => z.event_id as string),
      umgeschrieben: vorb.umgeschrieben,
      ungueltig: vorb.ungueltig,
      nicht_uebernommen: nichtUebernommen,
      bleiben_auf_geraet: [...nurGeraet],
      uebernommen: einfuegen.length,
      vollstaendig: nichtUebernommen.length === 0,
    });
  },
);
