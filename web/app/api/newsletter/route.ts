// Newsletter-Anmeldung: speichert die E-Mail-Adresse in Supabase (newsletter_anmeldungen).
// Vorerst ohne Double-Opt-in – es geht nur darum, keine Anmeldung zu verlieren.
import { absenderIp, antwort, emailGueltig, schreibClient, text, zuVieleAnfragen } from "@/lib/formulare";

export async function POST(request: Request) {
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

  if (zuVieleAnfragen("newsletter", absenderIp(request.headers), 5, 60 * 60 * 1000)) {
    return antwort(429, { fehler: "Zu viele Anmeldungen in kurzer Zeit. Bitte versuch es später noch einmal." });
  }

  const db = schreibClient();
  if (!db) return antwort(503, { fehler: "Die Anmeldung ist gerade nicht möglich. Bitte versuch es später." });

  const { error } = await db.from("newsletter_anmeldungen").insert({ email, quelle: "website" });
  // 23505 = schon angemeldet → für den Nutzer genauso ein Erfolg (verrät nicht, ob die Adresse existiert)
  if (error && error.code !== "23505") {
    console.error(`Newsletter-Anmeldung fehlgeschlagen: ${error.code} ${error.message}`);
    return antwort(500, { fehler: "Das hat leider nicht geklappt. Bitte versuch es später noch einmal." });
  }
  return antwort(200, { ok: true });
}
