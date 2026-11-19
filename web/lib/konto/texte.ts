// Nutzerkonten – angezeigte Texte der Einwilligungen (Plan 5.3).
// ENTWURF bis Schritt 6: Die Wortlaute gehen in die anwaltliche Durchsicht. Ändert sich ein Text, wird die
// Version in TEXTVERSIONEN (konfig.ts) hochgezählt, und derselbe Wortlaut kommt als neue Zeile in
// public.einwilligungstexte. Ein Test vergleicht dann Prüfsummen (Plan 4.4, 16.1).
// Erklärtexte per du (Entscheidung des Auftraggebers vom 17.11.2026, auch für die Datenschutz-Erklärtexte hier; die
// Datenschutzerklärung selbst bleibt unverändert), Häkchen-Sätze in der Ich-Form der erklärenden Person.

export const TEXT = {
  einleitung: {
    titel: "Was interessiert dich?",
    text: "Ein paar kurze Fragen, damit wir dir passende Events vorschlagen können. Am Ende entscheidest du, ob wir deine Antworten speichern.",
  },
  mindestalter: "Ich bin mindestens 16 Jahre alt.",
  // Fassung interessen-2026-11-2 (19.11.2026): Widerrufssatz per du (Wunsch des Auftraggebers).
  // Vorher (interessen-2026-11): „Ich kann das jederzeit im Konto widerrufen. Dann werden meine Antworten sofort gelöscht.“
  personalisierung:
    "Ich willige ein, dass dies.das meine Antworten in meinem Konto speichert und zusammen mit meiner Merkliste nutzt, " +
    "um mir passende Events vorzuschlagen. Sensible Events (siehe unten) fließen nie in Empfehlungen ein. Du kannst das " +
    "jederzeit im Konto widerrufen. Dann werden deine Antworten sofort gelöscht.",
  sensibelErklaerung:
    "Manche Events lassen Rückschlüsse auf sehr persönliche Dinge zu: Gesundheit, Religion oder Weltanschauung, sexuelle " +
    "Orientierung oder geschlechtliche Identität, politische Meinung, Gewerkschaftszugehörigkeit oder ethnische Herkunft. " +
    "Merkst du dir solche Events, speichern wir sie ohne deine ausdrückliche Einwilligung nur auf dem Gerät, auf dem du " +
    "sie gemerkt hast, und nicht in deinem Konto. Auf anderen Geräten siehst du sie dann nicht. Für Empfehlungen und " +
    "Statistiken nutzen wir sie nie, auch nicht mit Einwilligung.",
  // Fassung sensible-events-2026-11-2 (19.11.2026): Widerrufssatz per du (Wunsch des Auftraggebers).
  // Vorher (sensible-events-2026-11): „Ich kann das jederzeit im Konto widerrufen. Dann werden sie aus meinem Konto entfernt.“
  sensibel:
    "Ich willige ausdrücklich ein, dass dies.das auch solche Events, die ich mir merke, in meinem Konto speichert, damit " +
    "sie auf allen meinen Geräten verfügbar sind. Du kannst das jederzeit im Konto widerrufen. Dann werden sie aus deinem " +
    "Konto entfernt.",
  widerspruchErklaerung:
    "Wir zählen anonym, wie oft Events gemerkt werden, um zu sehen, was in Düsseldorf beliebt ist (berechtigtes Interesse, " +
    "Art. 6 Abs. 1 lit. f DSGVO). Wer was gemerkt hat, sieht dabei niemand, und sensible Events zählen nie mit. Du kannst " +
    "dem jederzeit widersprechen:",
  widerspruch: "Meine Merkliste nicht mitzählen. (Auch später im Konto.)",
  // Fassung geburtstagsmail-2026-11-3 (19.11.2026): Widerrufssatz per du (Wunsch des Auftraggebers).
  // Vorher -2 (E16): „… Ich kann das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen.“
  // Davor -1: „Dafür speichert dies.das mein Geburtsdatum. … Dann wird mein Geburtsdatum gelöscht.“
  geburtstag:
    "Ich möchte an meinem Geburtstag eine Mail von dies.das bekommen, mit Glückwünschen und Event-Tipps für den Tag. " +
    "Dafür nutzt dies.das mein Geburtsdatum aus meinem Konto. Du kannst das jederzeit im Konto oder über den " +
    "Abmeldelink in jeder Mail widerrufen.",
  // Art.-13-Hinweis zu den Pflichtangaben (E16), Schritt „Über dich“ und Konto-Seite
  stammdaten: {
    titel: "Noch kurz zu dir",
    text:
      "Name und Geburtsdatum sind Pflichtangaben für dein Konto. Mit dem Geburtsdatum prüfen wir, ob du mindestens " +
      "16 Jahre alt bist. Deinen Namen brauchen wir für Ticketkäufe über dein Konto und um dich persönlich anzusprechen. Ändern kannst du beides " +
      "jederzeit im Konto.",
  },
  widerrufSensibel:
    "Sensible Events entfernen wir aus deinem Konto. Auf diesem Gerät bleiben sie gemerkt, auf deinen anderen Geräten verschwinden sie.",
  art13: "Wir nutzen deine Adresse für die Anmeldung und dein Konto.",
  nutzungsbedingungen:
    "Mit „Konto anlegen“ akzeptierst du unsere Nutzungsbedingungen (mit Widerrufsbelehrung). Wie wir deine Daten " +
    "verarbeiten, steht in der Datenschutzerklärung.",
} as const;

/**
 * Gestufte Anzeige (Entscheidung des Auftraggebers vom 17.11.2026, laut ihm vom Anwalt freigegeben): je Häkchen
 * höchstens zwei Sätze sichtbar, der Rest unter „Mehr dazu“. Der Wortlaut bleibt unverändert und vollständig auf der
 * Seite: kurz + " " + mehr ergibt genau den Text, der als Nachweis gespeichert ist (Test in tests/konto-texte.test.ts).
 * Satzgrenze: Satzzeichen, Leerraum, dann ein Großbuchstabe (so bleiben „Abs. 1 lit. f“ und „dies.das“ ganz).
 */
export function ersteSaetze(text: string, anzahl: number): { kurz: string; mehr: string } {
  const teile = text.split(/(?<=[.!?:])\s+(?=[A-ZÄÖÜ])/);
  return { kurz: teile.slice(0, anzahl).join(" "), mehr: teile.slice(anzahl).join(" ") };
}

export const GESTUFT = {
  personalisierung: ersteSaetze(TEXT.personalisierung, 2),
  sensibelErklaerung: ersteSaetze(TEXT.sensibelErklaerung, 1),
  sensibel: ersteSaetze(TEXT.sensibel, 1),
  widerspruchErklaerung: ersteSaetze(TEXT.widerspruchErklaerung, 1),
  geburtstag: ersteSaetze(TEXT.geburtstag, 2),
} as const;

/**
 * Wortlaute, wie sie als Nachweis in public.einwilligungstexte stehen (Plan 4.4), je Art. Vom Anwalt freigegeben
 * (Mitteilung des Auftraggebers vom 17.11.2026). Das SQL erzeugt web/scripts/einwilligungstexte-sql.mjs aus dieser
 * Konstante; der Test tests/konto-texte.test.ts vergleicht die Prüfsummen im SQL mit diesem Code.
 * Diese Datei darf keine Imports haben: Das Skript lädt sie direkt mit Node.
 */
export const NACHWEIS_TEXT = {
  mindestalter: {
    zweck: "Bestätigung des Mindestalters von 16 Jahren (Registrierung bzw. /konto/willkommen)",
    text: TEXT.mindestalter,
  },
  nutzungsbedingungen: {
    zweck: "Annahme der Nutzungsbedingungen bei der Registrierung",
    text: TEXT.nutzungsbedingungen,
  },
  personalisierung: {
    zweck: "Einwilligung (a): Interessen speichern und persönliche Vorschläge",
    text: TEXT.personalisierung,
  },
  sensible_events: {
    zweck: "Ausdrückliche Einwilligung (b) nach Art. 9 Abs. 2 lit. a DSGVO: sensible Events im Konto speichern",
    text: `Datenschutz ist uns hier besonders wichtig. ${TEXT.sensibelErklaerung}\n\n${TEXT.sensibel}`,
  },
  analyse: {
    zweck: "Hinweis (c) auf das Widerspruchsrecht nach Art. 21 Abs. 4 DSGVO zur anonymen Beliebtheits-Zählung",
    text: `Dein Widerspruchsrecht: ${TEXT.widerspruchErklaerung}\n\n${TEXT.widerspruch}`,
  },
  geburtstagsmail: {
    zweck: "Einwilligung (d) nach Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG: Geburtstagsmail (Geburtsdatum ist Pflichtangabe, E16)",
    text: TEXT.geburtstag,
  },
} as const;
