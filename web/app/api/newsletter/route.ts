// Newsletter-Anmeldung mit Double-Opt-in (Plan Admin-Dashboard 4.9, Stufe 4): legt die Anmeldung an; die
// Bestätigungsmail schickt der Job pipeline/newsletter_bestaetigung.py (alle 15 Minuten). Erst nach dem Klick auf den
// Link in der Mail ist die Adresse bestätigt. Die Antwort ist immer gleich – sie verrät nicht, ob eine Adresse
// schon angemeldet ist.
import { anmeldungPlanen, type Bestand } from "@/lib/newsletter";
import { jobAnstossen } from "@/lib/job-anstoss";
import { absenderIp, antwort, emailGueltig, schreibClient, text, zuGross, zuVieleAnfragen } from "@/lib/formulare";

export async function POST(request: Request) {
  if (zuGross(request, 4 * 1024)) return antwort(413, { fehler: "Ungültige Anfrage." });
  // Grobes Bremslimit vor dem Einlesen: jede Anfrage zählt (auch Honeypot-Treffer und Tippfehler)
  const ip = absenderIp(request.headers);
  if (zuVieleAnfragen("newsletter-anfragen", ip, 20, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Anfragen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }
  let daten: Record<string, unknown>;
  try {
    daten = await request.json();
  } catch {
    return antwort(400, { fehler: "Ungültige Anfrage." });
  }

  // Honeypot: Menschen sehen das Feld nicht, Bots füllen es aus → still „erfolgreich“ verwerfen
  if (text(daten.website, 200)) return antwort(200, { ok: true });

  const email = text(daten.email, 254)?.toLowerCase() ?? "";
  if (!emailGueltig(email)) return antwort(400, { fehler: "Bitte gib eine gültige E-Mail-Adresse ein." });
  if (zuVieleAnfragen("newsletter", ip, 5, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Anmeldungen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }

  const db = schreibClient();
  if (!db) return antwort(503, { fehler: "Die Anmeldung ist gerade nicht möglich. Bitte versuch es später." });

  const fehlgeschlagen = () => antwort(500, { fehler: "Das hat leider nicht geklappt. Bitte versuch es später noch einmal." });
  const { data: bestand, error: f1 } = await db
    .from("newsletter_anmeldungen")
    .select("id, bestaetigt_am, bestaetigung_gesendet_am, bestaetigung_zugestellt_am, mails_gesendet")
    .ilike("email", email.replace(/[\\%_]/g, (z) => `\\${z}`))
    .maybeSingle();
  if (f1) {
    console.error(`Newsletter-Anmeldung: Bestand nicht lesbar (${f1.code ?? "fehler"})`);
    return fehlgeschlagen();
  }
  const plan = anmeldungPlanen(bestand as Bestand | null);
  if (plan === "anlegen") {
    const { error } = await db.from("newsletter_anmeldungen").insert({ email, quelle: "website" });
    // 23505: gleichzeitig angelegt → für den Nutzer genauso ein Erfolg
    if (error && error.code !== "23505") {
      console.error(`Newsletter-Anmeldung fehlgeschlagen: ${error.code} ${error.message}`);
      return fehlgeschlagen();
    }
  } else if (plan === "erneut_senden" && bestand) {
    const { error } = await db.from("newsletter_anmeldungen").update({ bestaetigung_gesendet_am: null, bestaetigung_zugestellt_am: null }).eq("id", bestand.id).is("bestaetigt_am", null);
    if (error) {
      console.error(`Newsletter-Anmeldung: erneuter Versand nicht vorgemerkt (${error.code ?? "fehler"})`);
      return fehlgeschlagen();
    }
  }
  // Bestätigungsmail sofort anstoßen (der 15-Minuten-Zeitplan von GitHub ist unzuverlässig); höchstens ein Lauf je
  // 5 Minuten, der Job prüft NEWSLETTER_AKTIV selbst
  // Auch bei erneutem Absenden einer Adresse, deren Mail noch aussteht (häufig: „kam nichts, nochmal probieren“)
  const wartet = !!bestand && !bestand.bestaetigt_am && !bestand.bestaetigung_zugestellt_am;
  if (plan === "anlegen" || plan === "erneut_senden" || wartet) jobAnstossen("newsletter", { aufgabe: "senden" });
  return antwort(200, { ok: true });
}
