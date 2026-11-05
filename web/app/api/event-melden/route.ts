// „Event melden“: nimmt das Formular (multipart, optional mit Bild) entgegen, prüft alles serverseitig,
// lädt das Bild in den privaten Bucket „event-meldungen“ und legt eine Meldung mit status = 'neu' an.
// Veröffentlicht wird erst, wenn ein Admin die Meldung im Dashboard freigibt.
import { heuteBerlin, plusTage } from "@/lib/datum";
import { absenderIp, antwort, emailGueltig, schreibClient, text, zuVieleAnfragen } from "@/lib/formulare";

const KATEGORIEN = new Set([
  "kultur", "musik", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family", "dating", "sonstiges",
]);
const MAX_BILD = 2 * 1024 * 1024; // = Grenze des Buckets
const BILD_TYPEN: Record<string, string> = { "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp" };

/** Dateityp an den ersten Bytes erkennen (nicht der Angabe des Browsers vertrauen). */
function bildTyp(b: Uint8Array): string | null {
  if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return "image/jpeg";
  if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return "image/png";
  if (String.fromCharCode(...b.slice(0, 4)) === "RIFF" && String.fromCharCode(...b.slice(8, 12)) === "WEBP") return "image/webp";
  return null;
}

const DATUM = /^\d{4}-\d{2}-\d{2}$/;
const UHRZEIT = /^([01]\d|2[0-3]):[0-5]\d$/;

export async function POST(request: Request) {
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return antwort(400, { fehler: "Ungültige Anfrage." });
  }

  // Honeypot: Bots füllen das unsichtbare Feld → still „erfolgreich“ verwerfen
  if (text(form.get("website"), 200)) return antwort(200, { ok: true });

  if (zuVieleAnfragen("event-melden", absenderIp(request.headers), 5, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Meldungen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }

  const felder: Record<string, string> = {};
  const heute = heuteBerlin(new Date());

  const titel = text(form.get("titel"), 150);
  if (!titel || titel.length < 3) felder.titel = "Bitte gib einen Titel an (mind. 3 Zeichen).";

  const kategorie = text(form.get("kategorie"), 30);
  if (!kategorie || !KATEGORIEN.has(kategorie)) felder.kategorie = "Bitte wähle eine Kategorie.";

  const datum = text(form.get("datum"), 10);
  if (!datum || !DATUM.test(datum)) felder.datum = "Bitte gib ein Datum an.";
  else if (datum < heute) felder.datum = "Das Datum liegt in der Vergangenheit.";
  else if (datum > plusTage(heute, 400)) felder.datum = "Bitte melde nur Events in den nächsten 13 Monaten.";

  const datumBis = text(form.get("datum_bis"), 10);
  if (datumBis && (!DATUM.test(datumBis) || (datum && datumBis < datum))) felder.datum_bis = "Das Enddatum muss nach dem Startdatum liegen.";
  else if (datumBis && datum && datumBis > plusTage(datum, 366)) felder.datum_bis = "Der Zeitraum darf höchstens ein Jahr lang sein.";

  const uhrzeit = text(form.get("uhrzeit"), 5);
  if (uhrzeit && !UHRZEIT.test(uhrzeit)) felder.uhrzeit = "Bitte gib die Uhrzeit als HH:MM an.";

  const ort = text(form.get("ort"), 150);
  if (!ort || ort.length < 2) felder.ort = "Bitte gib den Veranstaltungsort an.";

  const adresse = text(form.get("adresse"), 200);
  const preis = form.get("kostenlos") === "ja" ? "kostenlos" : text(form.get("preis"), 80);

  const beschreibung = text(form.get("beschreibung"), 2000);
  if (!beschreibung || beschreibung.length < 20) felder.beschreibung = "Bitte beschreibe das Event in ein paar Sätzen (mind. 20 Zeichen).";

  let link = text(form.get("link"), 500);
  if (link) {
    if (!/^https?:\/\//i.test(link)) link = `https://${link}`;
    try {
      const u = new URL(link);
      if (!["http:", "https:"].includes(u.protocol) || !u.hostname.includes(".")) throw new Error();
    } catch {
      felder.link = "Bitte gib einen gültigen Link an (z.B. https://…).";
    }
  }

  const kontaktName = text(form.get("kontakt_name"), 100);
  const kontaktEmail = text(form.get("kontakt_email"), 254)?.toLowerCase() ?? "";
  if (!emailGueltig(kontaktEmail)) felder.kontakt_email = "Bitte gib eine gültige E-Mail-Adresse an (für Rückfragen).";
  const kontaktRolle = form.get("kontakt_rolle") === "besucher" ? "besucher" : "veranstalter";
  const anmerkung = text(form.get("anmerkung"), 1000);

  if (form.get("datenschutz") !== "ja") felder.datenschutz = "Bitte bestätige die Datenschutzhinweise.";

  // Bild (optional)
  const bild = form.get("bild");
  let bildDaten: { bytes: Uint8Array; typ: string } | null = null;
  if (bild instanceof File && bild.size > 0) {
    if (bild.size > MAX_BILD) felder.bild = "Das Bild ist zu groß (max. 2 MB).";
    else {
      const bytes = new Uint8Array(await bild.arrayBuffer());
      const typ = bildTyp(bytes);
      if (!typ) felder.bild = "Bitte lade ein JPG-, PNG- oder WebP-Bild hoch.";
      else bildDaten = { bytes, typ };
    }
    if (form.get("bild_rechte") !== "ja") felder.bild_rechte = "Bitte bestätige, dass du das Bild verwenden darfst.";
  }

  if (Object.keys(felder).length) {
    return antwort(400, { fehler: "Bitte prüfe die markierten Felder.", felder });
  }

  const db = schreibClient();
  if (!db) return antwort(503, { fehler: "Das Melden ist gerade nicht möglich. Bitte versuch es später." });

  let bildPfad: string | null = null;
  if (bildDaten) {
    bildPfad = `meldungen/${crypto.randomUUID()}.${BILD_TYPEN[bildDaten.typ]}`;
    const { error } = await db.storage.from("event-meldungen").upload(bildPfad, bildDaten.bytes, {
      contentType: bildDaten.typ,
      upsert: false,
    });
    if (error) {
      console.error(`Event-Meldung: Bild-Upload fehlgeschlagen: ${error.message}`);
      return antwort(500, { fehler: "Das Bild konnte nicht hochgeladen werden. Bitte versuch es ohne Bild oder später noch einmal." });
    }
  }

  const { error } = await db.from("event_meldungen").insert({
    titel,
    kategorie,
    datum,
    datum_bis: datumBis || null,
    uhrzeit: uhrzeit || null,
    ort,
    adresse,
    preis,
    beschreibung,
    link: link || null,
    bild_pfad: bildPfad,
    bild_rechte: bildDaten ? true : false,
    kontakt_name: kontaktName,
    kontakt_email: kontaktEmail,
    kontakt_rolle: kontaktRolle,
    anmerkung,
  });
  if (error) {
    console.error(`Event-Meldung fehlgeschlagen: ${error.code} ${error.message}`);
    return antwort(500, { fehler: "Das hat leider nicht geklappt. Bitte versuch es später noch einmal." });
  }
  return antwort(200, { ok: true });
}
