// „Event melden“: nimmt das Formular (multipart, optional mit Bild) entgegen, prüft alles serverseitig,
// kodiert das Bild neu (sharp: entfernt EXIF/GPS, zerstört Polyglot-Dateien), lädt es in den privaten
// Bucket „event-meldungen“ und legt eine Meldung mit status = 'neu' an.
// Veröffentlicht wird erst, wenn ein Admin die Meldung im Dashboard freigibt.
import { heuteBerlin, plusTage } from "@/lib/datum";
import {
  absenderIp, antwort, emailGueltig, kalenderdatum, schreibClient, text, zeile, zuGross, zuVieleAnfragen,
} from "@/lib/formulare";

const KATEGORIEN = new Set([
  "kultur", "musik", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family", "dating", "sonstiges",
]);
const MAX_BILD = 2 * 1024 * 1024; // = Grenze des Buckets (der Browser schickt ein verkleinertes JPEG)
const MAX_ANFRAGE = 3 * 1024 * 1024; // Bild + Textfelder; größere Anfragen werden gar nicht erst eingelesen
const MAX_KANTE = 1600;
const MAX_GLEICHZEITIG = 2; // gleichzeitige sharp-Neukodierungen im Prozess
let bildInArbeit = 0;

/** Dateityp an den ersten Bytes erkennen (nicht der Angabe des Browsers vertrauen). */
function bildTyp(b: Uint8Array): string | null {
  if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return "image/jpeg";
  if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return "image/png";
  if (String.fromCharCode(...b.slice(0, 4)) === "RIFF" && String.fromCharCode(...b.slice(8, 12)) === "WEBP") return "image/webp";
  return null;
}

/**
 * Bild neu kodieren: Ausrichtung übernehmen, auf max. 1600 px verkleinern, als JPEG ohne Metadaten
 * speichern. Gibt null zurück, wenn sharp fehlt oder das Bild kaputt ist.
 */
async function bildNeuKodieren(bytes: Uint8Array): Promise<Buffer | null> {
  try {
    const { default: sharp } = await import("sharp");
    return await sharp(bytes, { limitInputPixels: 50_000_000, failOn: "error" })
      .rotate()
      .resize({ width: MAX_KANTE, height: MAX_KANTE, fit: "inside", withoutEnlargement: true })
      .flatten({ background: "#ffffff" })
      .jpeg({ quality: 82, mozjpeg: true })
      .toBuffer();
  } catch (err) {
    console.error(`Event-Meldung: Bild nicht verarbeitbar: ${err instanceof Error ? err.message : err}`);
    return null;
  }
}

const UHRZEIT = /^([01]\d|2[0-3]):[0-5]\d$/;

export async function POST(request: Request) {
  if (zuGross(request, MAX_ANFRAGE)) {
    return antwort(413, { fehler: "Die Meldung ist zu groß. Bitte verwende ein kleineres Bild." });
  }
  // Grobes Bremslimit VOR dem Einlesen: jede Anfrage zählt (auch Honeypot-Treffer und fehlerhafte).
  // Großzügig, damit Tippfehler-Korrekturen niemanden aussperren; gültige Meldungen zählt das 2. Limit.
  const ip = absenderIp(request.headers);
  if (zuVieleAnfragen("event-melden-anfragen", ip, 20, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Anfragen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return antwort(400, { fehler: "Ungültige Anfrage." });
  }

  // Honeypot: Bots füllen das unsichtbare Feld → still „erfolgreich“ verwerfen
  if (text(form.get("website"), 200)) return antwort(200, { ok: true });

  const felder: Record<string, string> = {};
  const heute = heuteBerlin(new Date());

  const titel = zeile(form.get("titel"), 150);
  if (!titel || titel.length < 3) felder.titel = "Bitte gib einen Titel an (mind. 3 Zeichen).";

  const kategorie = zeile(form.get("kategorie"), 30);
  if (!kategorie || !KATEGORIEN.has(kategorie)) felder.kategorie = "Bitte wähle eine Kategorie.";

  const datum = zeile(form.get("datum"), 10);
  if (!kalenderdatum(datum)) felder.datum = "Bitte gib ein gültiges Datum an.";
  else if (datum! < heute) felder.datum = "Das Datum liegt in der Vergangenheit.";
  else if (datum! > plusTage(heute, 400)) felder.datum = "Bitte melde nur Events in den nächsten 13 Monaten.";

  const datumBis = zeile(form.get("datum_bis"), 10);
  if (datumBis && (!kalenderdatum(datumBis) || (datum && datumBis < datum))) felder.datum_bis = "Das Enddatum muss ein gültiges Datum nach dem Startdatum sein.";
  else if (datumBis && datum && kalenderdatum(datum) && datumBis > plusTage(datum, 366)) felder.datum_bis = "Der Zeitraum darf höchstens ein Jahr lang sein.";

  const uhrzeit = zeile(form.get("uhrzeit"), 5);
  if (uhrzeit && !UHRZEIT.test(uhrzeit)) felder.uhrzeit = "Bitte gib die Uhrzeit als HH:MM an.";

  const ort = zeile(form.get("ort"), 150);
  if (!ort || ort.length < 2) felder.ort = "Bitte gib den Veranstaltungsort an.";

  const adresse = zeile(form.get("adresse"), 200);
  const preis = form.get("kostenlos") === "ja" ? "kostenlos" : zeile(form.get("preis"), 80);

  const beschreibung = text(form.get("beschreibung"), 2000);
  if (!beschreibung || beschreibung.length < 20) felder.beschreibung = "Bitte beschreibe das Event in ein paar Sätzen (mind. 20 Zeichen).";

  // Link: normalisiert speichern (u.href) – keine Zeilenumbrüche, kein Markdown, nur http(s)
  let link: string | null = null;
  const linkRoh = zeile(form.get("link"), 500);
  if (linkRoh) {
    try {
      const u = new URL(/^https?:\/\//i.test(linkRoh) ? linkRoh : `https://${linkRoh}`);
      if (!["http:", "https:"].includes(u.protocol) || !u.hostname.includes(".") || u.username || u.password) throw new Error();
      link = u.href.slice(0, 500);
    } catch {
      felder.link = "Bitte gib einen gültigen Link an (z.B. https://…).";
    }
  }

  const kontaktName = zeile(form.get("kontakt_name"), 100);
  const kontaktEmail = zeile(form.get("kontakt_email"), 254)?.toLowerCase() ?? "";
  if (!emailGueltig(kontaktEmail)) felder.kontakt_email = "Bitte gib eine gültige E-Mail-Adresse an (für Rückfragen).";
  const kontaktRolle = form.get("kontakt_rolle") === "besucher" ? "besucher" : "veranstalter";
  const anmerkung = text(form.get("anmerkung"), 1000);

  if (form.get("datenschutz") !== "ja") felder.datenschutz = "Bitte bestätige die Datenschutzhinweise.";

  // Bild (optional): Größe, Signatur und Rechte prüfen – neu kodiert wird erst ganz unten
  const bild = form.get("bild");
  let bildBytes: Uint8Array | null = null;
  if (bild instanceof File && bild.size > 0) {
    if (form.get("bild_rechte") !== "ja") felder.bild_rechte = "Bitte bestätige, dass du das Bild verwenden darfst.";
    if (bild.size > MAX_BILD) felder.bild = "Das Bild ist zu groß (max. 2 MB).";
    else {
      bildBytes = new Uint8Array(await bild.arrayBuffer());
      if (!bildTyp(bildBytes)) felder.bild = "Bitte lade ein JPG-, PNG- oder WebP-Bild hoch.";
    }
  }

  if (Object.keys(felder).length) {
    return antwort(400, { fehler: "Bitte prüfe die markierten Felder.", felder });
  }
  if (zuVieleAnfragen("event-melden", ip, 5, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Meldungen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }

  // Teure Bildverarbeitung erst jetzt (gültige Meldung, Limit gezählt) und nie mehr als
  // MAX_GLEICHZEITIG Bilder auf einmal – schützt den Speicher des einen Node-Prozesses
  let bildJpeg: Buffer | null = null;
  if (bildBytes) {
    if (bildInArbeit >= MAX_GLEICHZEITIG) {
      return antwort(503, { fehler: "Gerade ist viel los. Bitte versuch es in einer Minute noch einmal." });
    }
    bildInArbeit++;
    try {
      bildJpeg = await bildNeuKodieren(bildBytes);
    } finally {
      bildInArbeit--;
    }
    if (!bildJpeg) {
      return antwort(400, {
        fehler: "Bitte prüfe die markierten Felder.",
        felder: { bild: "Das Bild konnte nicht verarbeitet werden. Bitte versuch ein anderes oder melde ohne Bild." },
      });
    }
  }

  const db = schreibClient();
  if (!db) return antwort(503, { fehler: "Das Melden ist gerade nicht möglich. Bitte versuch es später." });

  let bildPfad: string | null = null;
  if (bildJpeg) {
    bildPfad = `meldungen/${crypto.randomUUID()}.jpg`;
    const { error } = await db.storage.from("event-meldungen").upload(bildPfad, bildJpeg, {
      contentType: "image/jpeg",
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
    link,
    bild_pfad: bildPfad,
    bild_rechte: !!bildPfad,
    kontakt_name: kontaktName,
    kontakt_email: kontaktEmail,
    kontakt_rolle: kontaktRolle,
    anmerkung,
  });
  if (error) {
    console.error(`Event-Meldung fehlgeschlagen: ${error.code} ${error.message}`);
    // Kein verwaistes Bild zurücklassen
    if (bildPfad) {
      const aufraeumen = await db.storage.from("event-meldungen").remove([bildPfad])
        .catch((e: unknown) => ({ error: e instanceof Error ? e : new Error(String(e)) }));
      if (aufraeumen.error) {
        console.error(`Event-Meldung: verwaistes Bild ${bildPfad} nicht gelöscht – bitte im Storage entfernen: ${aufraeumen.error.message}`);
      }
    }
    return antwort(500, { fehler: "Das hat leider nicht geklappt. Bitte versuch es später noch einmal." });
  }
  return antwort(200, { ok: true });
}
