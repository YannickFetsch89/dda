// Eigene Daten herunterladen (Plan 5.7): Konto mit Name, Interessen, Geburtsdatum, Schalter, Einwilligungs-Verlauf mit Wortlaut,
// Merkliste mit Titel und Datum. Kein Passwort-Hash, keine Kennzeichnung sensibler Events.
import { kontoDienstClient } from "@/lib/konto/clients";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";

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
      hinweis: "Eine vollständige Auskunft nach Art. 15 DSGVO bekommst du auch per Mail an moin@rocktician.com.",
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
    antwort.headers.set("Content-Disposition", 'attachment; filename="diesdas-konto.json"');
    return antwort;
  },
);
