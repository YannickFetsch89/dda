// Eigene Daten herunterladen (Plan 5.7): Konto mit Name, Interessen, Geburtsdatum, Schalter, Einwilligungs-Verlauf mit Wortlaut,
// Merkliste mit Titel und Datum. Kein Passwort-Hash, keine Kennzeichnung sensibler Events.
import { kontoDienstClient } from "@/lib/konto/clients";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

/**
 * Angaben nach Art. 15 Abs. 1 und 2 DSGVO (17.11.2026: der Download heißt jetzt „vollständige Auskunft“). Inhaltlich
 * aus der Datenschutzerklärung, Abschnitt 13 (web/app/datenschutz/konto-abschnitt.tsx) – bei Änderungen dort mitziehen.
 */
const AUSKUNFT = {
  verantwortlicher: "Rocktician e. K., Inhaber Yannick Fetsch, Erkrather Str. 401, 40231 Düsseldorf, moin@rocktician.com",
  zwecke_und_rechtsgrundlagen: [
    { zweck: "Konto führen, Anmeldung", daten: "Mailadresse, Passwort (nur als Hash bei Supabase), Zeitpunkte, Sitzungen", grundlage: "Art. 6 Abs. 1 lit. b DSGVO" },
    { zweck: "Pflichtangaben", daten: "Vorname, Nachname, Geburtsdatum (Altersprüfung ab 16, Ticketkäufe über das Konto)", grundlage: "Art. 6 Abs. 1 lit. b DSGVO" },
    { zweck: "Merkliste im Konto", daten: "gemerkte Events, Zeitpunkt", grundlage: "Art. 6 Abs. 1 lit. b DSGVO" },
    { zweck: "Besonders schützenswerte Events im Konto", daten: "gemerkte Events dieser Art", grundlage: "Art. 9 Abs. 2 lit. a i. V. m. Art. 6 Abs. 1 lit. a DSGVO (nur mit Einwilligung)" },
    { zweck: "Interessen und persönliche Vorschläge", daten: "Antworten aus dem Fragebogen, Merkliste", grundlage: "Art. 6 Abs. 1 lit. a DSGVO (nur mit Einwilligung)" },
    { zweck: "Anonyme Beliebtheits-Zählung", daten: "Anzahl der Merkungen je Event, ohne Personenbezug im Ergebnis", grundlage: "Art. 6 Abs. 1 lit. f DSGVO, Widerspruch jederzeit möglich" },
    { zweck: "Geburtstagsmail", daten: "Geburtsdatum, Datum der letzten Mail", grundlage: "Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG (nur mit Einwilligung)" },
    { zweck: "Nachweis von Einwilligungen und Altersbestätigung", daten: "Zeitpunkt, Art, Fassung des Textes", grundlage: "Art. 6 Abs. 1 lit. b und c, Art. 7 Abs. 1 DSGVO" },
    { zweck: "Schutz vor Missbrauch", daten: "IP-Adresse, gehashte Mailadresse (nur im Arbeitsspeicher, rund eine Stunde)", grundlage: "Art. 6 Abs. 1 lit. f DSGVO" },
  ],
  empfaenger: [
    "Supabase, Inc. (Datenbank und Anmeldung, Server der AWS in Frankfurt) als Auftragsverarbeiter",
    "unser Hosting-Anbieter (Website und Versand der Konto-Mails) als Auftragsverarbeiter",
  ],
  drittland: "Ein Zugriff durch Supabase, Inc. oder deren Unterauftragsverarbeiter aus Drittländern ist nicht ausgeschlossen. Grundlage sind die Standardvertragsklauseln der EU-Kommission (Art. 46 Abs. 2 lit. c DSGVO).",
  speicherdauer: [
    "Konto und Pflichtangaben: bis zur Löschung des Kontos, ohne Nutzung höchstens 24 Monate",
    "Einwilligungsabhängige Daten: bis zum Widerruf, spätestens mit dem Konto",
    "Anmeldeprotokolle bei Supabase: 7 Tage; Datensicherungen bei Supabase: bis zu 7 Tage",
  ],
  herkunft: "Alle Daten hast du selbst angegeben oder sie sind bei der Nutzung deines Kontos entstanden.",
  automatisierte_entscheidungen: "Keine automatisierte Entscheidung nach Art. 22 DSGVO. Persönliche Vorschläge wählen nur Events aus.",
  deine_rechte: "Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung (Art. 18), Datenübertragbarkeit (Art. 20), Widerspruch (Art. 21), Widerruf von Einwilligungen (Art. 7 Abs. 3) – vieles direkt im Konto, sonst per Mail an moin@rocktician.com. Beschwerde bei einer Aufsichtsbehörde, z. B. der Landesbeauftragten für Datenschutz und Informationsfreiheit NRW.",
  nicht_in_dieser_datei: "Anmeldeprotokolle bei Supabase (IP-Adresse, Zeitpunkt; 7 Tage) und Server-Logfiles (30 Tage). Eine Kopie bekommst du auf Anfrage per Mail an moin@rocktician.com.",
};

export const GET = kontoRoute(
  { anmeldung: true, ohneMindestalter: true, limit: { name: "export", max: 5, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const p = ctx.profil!;
    const s = ctx.sitzung!;
    const db = ctx.db!;

    const [einw, texte, merk] = await Promise.all([
      db.from("einwilligungen").select("art, erteilt, textversion, handlung, zeitpunkt").order("zeitpunkt"),
      db.from("einwilligungstexte").select("version, text"),
      db.from("merkliste").select("event_id, gemerkt_am").order("gemerkt_am", { ascending: false }),
    ]);
    if (einw.error || texte.error || merk.error) return kontoAntwort(503, { fehler: "Der Export ist gerade nicht möglich." });

    // Titel und Datum der gemerkten Events (auch abgelehnte, damit der Export vollständig ist)
    const ids = (merk.data ?? []).map((z) => z.event_id as string);
    const titel = new Map<string, { titel: string; datum: string }>();
    const dienst = kontoDienstClient();
    let letzteAnmeldung: string | null = null;
    if (dienst) {
      for (let i = 0; i < ids.length; i += 200) {
        const { data } = await dienst.from("events").select("id, titel, datum").in("id", ids.slice(i, i + 200));
        for (const e of data ?? []) titel.set(e.id as string, { titel: e.titel as string, datum: e.datum as string });
      }
      const { data } = await dienst.auth.admin.getUserById(s.nutzerId);
      letzteAnmeldung = data.user?.last_sign_in_at ?? null;
    }
    const wortlaut = new Map((texte.data ?? []).map((t) => [t.version as string, t.text as string]));

    const inhalt = {
      erstellt: new Date().toISOString(),
      hinweis:
        "Auskunft nach Art. 15 DSGVO: oben die Angaben zur Verarbeitung, darunter eine Kopie deiner Daten im Konto. " +
        "Fragen oder eine Auskunft per Mail: moin@rocktician.com.",
      auskunft_art_15: AUSKUNFT,
      konto: { email: s.email, vorname: p.vorname, nachname: p.nachname, angelegt: p.erstellt_am, letzte_anmeldung: letzteAnmeldung },
      interessen: p.praeferenzen ?? {},
      geburtsdatum: p.geburtsdatum,
      letzte_geburtstagsmail: p.geburtstagsmail_zuletzt,
      schalter: {
        interessen_und_empfehlungen: p.personalisierung,
        sensible_events_im_konto: p.sensible_events_erlaubt,
        anonym_mitzaehlen: p.analyse_erlaubt,
        geburtstagsmail: p.geburtstagsmail,
      },
      einwilligungen: (einw.data ?? []).map((e) => ({ ...e, wortlaut: wortlaut.get(e.textversion as string) ?? null })),
      merkliste: (merk.data ?? []).map((z) => ({
        event_id: z.event_id,
        gemerkt_am: z.gemerkt_am,
        titel: titel.get(z.event_id as string)?.titel ?? null,
        datum: titel.get(z.event_id as string)?.datum ?? null,
      })),
    };
    const antwort = kontoAntwort(200, inhalt);
    antwort.headers.set("Content-Disposition", 'attachment; filename="diesdas-auskunft.json"');
    return antwort;
  },
);
