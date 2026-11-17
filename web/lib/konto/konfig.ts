// Nutzerkonten – Schalter, Grenzen und Textversionen (Plan docs/plan-nutzerkonten-2026-11-16.md).
// Ohne Abhängigkeiten, auch in Client-Komponenten nutzbar (keine Secrets hier).

/**
 * Schalter KONTEN_AKTIV (E10): Ist er aus, antworten alle Routen unter /api/konto/* mit 404 und fassen keine
 * Tabelle an. Gesetzt in web/.env.local (wie die Supabase-Variablen). Nur „1“ oder „true“ schalten ein.
 */
export function kontenAktiv(): boolean {
  const wert = process.env.KONTEN_AKTIV?.trim().toLowerCase();
  return wert === "1" || wert === "true";
}

/** Cookie-Namen (Plan 3.2) */
export const SITZUNG_COOKIE = "ddd_sitzung";
export const HINWEIS_COOKIE = "ddd_konto";

/** Laufzeiten (Plan 3.2, 5.1 Schritt 9) */
export const SITZUNG_SEKUNDEN = 30 * 24 * 60 * 60;
export const RESET_SITZUNG_SEKUNDEN = 60 * 60;
/** Erneuern, wenn das Access-Token in weniger als so vielen Sekunden abläuft */
export const ERNEUERN_VOR_SEKUNDEN = 60;

/** Grenzen */
export const MERKLISTE_MAX = 500; // auch im Trigger merkliste_vor_insert (database/konten_2026-11-16.sql)
export const UEBERNAHME_MAX_IDS = 1000;
export const UEBERNAHME_MAX_BYTES = 48 * 1024;
export const BODY_MAX_BYTES = 4 * 1024;
export const VORLIEBEN_MAX_JE_LISTE = 60;

/**
 * Textversionen der Einwilligungen (Plan 3.4, 4.4). Die Route setzt sie, nie der Body. Bei jeder Änderung eines
 * angezeigten Textes wird die Version hochgezählt, und dieselbe Version kommt als neue Zeile in
 * public.einwilligungstexte (Schritt 6). Die Wortlaute selbst folgen mit Schritt 6.
 */
export const TEXTVERSIONEN = {
  mindestalter: "mindestalter-2026-11",
  nutzungsbedingungen: "nutzungsbedingungen-2026-11",
  personalisierung: "interessen-2026-11",
  sensible_events: "sensible-events-2026-11",
  analyse: "analyse-hinweis-2026-11",
  // -2: Datum ist seit E16 Pflichtangabe und bleibt beim Widerruf stehen (17.11.2026)
  geburtstagsmail: "geburtstagsmail-2026-11-2",
} as const;

export type EinwilligungArt = keyof typeof TEXTVERSIONEN;
export type Handlung =
  | "registrierung"
  | "abschlussseite"
  | "konto_schalter"
  | "interessen_aendern"
  | "abmeldelink"
  | "altersgrenze";

/** Feste Meldungen (Plan 5.1, 6). Fehltexte von Supabase werden nie durchgereicht. */
export const MELDUNG = {
  registriert:
    "Fast geschafft! Wir haben dir eine Mail geschickt. Bitte bestätige deine Adresse über den Link darin. " +
    "Hast du dich schon einmal registriert und noch nicht bestätigt, gilt das Passwort von damals.",
  anmeldenFalsch: "Mailadresse oder Passwort stimmen nicht.",
  nichtBestaetigt: "Bitte bestätige zuerst deine Mailadresse.",
  resetUnterwegs: "Wenn es ein Konto mit dieser Adresse gibt, ist eine Mail unterwegs.",
  bestaetigungUnterwegs: "Wenn es ein unbestätigtes Konto mit dieser Adresse gibt, ist eine neue Mail unterwegs.",
  linkFalsch: "Der Link oder Code stimmt nicht oder ist abgelaufen.",
  passwortGeaendert: "Dein Passwort ist geändert. Andere Geräte sind abgemeldet.",
  passwortRegel: "Das Passwort braucht mindestens 10 und höchstens 72 Zeichen.",
  zuViele: "Zu viele Versuche in kurzer Zeit. Bitte versuch es später noch einmal.",
  nichtVerfuegbar: "Konten sind gerade nicht verfügbar.",
  // Entscheidung des Auftraggebers vom 17.11.2026: Eine schon bestätigte Adresse wird bei der Registrierung genannt
  // (statt der neutralen Antwort aus Plan 5.1), damit niemand vergeblich auf eine Mail wartet.
  schonRegistriert: "Für diese Mailadresse gibt es schon ein Konto. Melde dich einfach an.",
  ungueltig: "Ungültige Anfrage.",
  unter16: "dies.das-Konten gibt es ab 16 Jahren. Dein Konto wird daher gelöscht.",
  geloescht: "Dein Konto und deine Merkliste sind gelöscht.",
} as const;
