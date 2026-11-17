"use client";
// Nutzerkonten – /konto/willkommen (Alter, Fragebogen, Abschluss) und /konto (Übersicht, Schalter, Passwort,
// Export, Löschen, Abmelden). Alle Daten kommen aus /api/konto/* (Plan 5.3, 5.7).
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { InteressenFragebogen, KEINE, type AbschlussWerte, type Antworten, type FragebogenDaten } from "./interessen-fragebogen";
import { Meldung, PasswortFeld, fehlerText, konto } from "./konto";
import { abmelden, lokalAbmelden, nurGeraetHochladen, uebernahmePruefen, zurueckAufsGeraet } from "@/lib/konto/merk-store";
import { TEXT } from "@/lib/konto/texte";

const UNTER16 = "dies.das-Konten gibt es ab 16 Jahren. Dein Konto wird daher gelöscht.";

interface Ich {
  email: string | null;
  angelegt: string;
  onboarding_fertig_am: string | null;
  mindestalter_bestaetigt: boolean;
  gesperrt: boolean;
  personalisierung: boolean;
  sensible_events_erlaubt: boolean;
  widerspruch_zaehlung: boolean;
  geburtstagsmail: boolean;
  geburtsdatum: string | null;
  vorname: string | null;
  nachname: string | null;
  praeferenzen: Partial<Antworten> & { version?: number };
}

type Laden = { art: "laden" } | { art: "abgemeldet" } | { art: "fehler"; text: string } | { art: "da"; ich: Ich };

function useIch(): [Laden, () => Promise<void>] {
  const router = useRouter();
  const [z, setZ] = useState<Laden>({ art: "laden" });
  const laden = useCallback(async () => {
    const a = await konto("ich");
    if (a.status === 401) {
      lokalAbmelden();
      setZ({ art: "abgemeldet" });
    } else if (a.status === 403 && a.daten.code === "passwort_setzen_noetig") {
      router.push("/konto/passwort-neu");
    } else if (a.status === 200) setZ({ art: "da", ich: a.daten as unknown as Ich });
    else setZ({ art: "fehler", text: fehlerText(a) });
  }, [router]);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden beim ersten Anzeigen
    void laden();
  }, [laden]);
  return [z, laden];
}

function Abgemeldet() {
  return (
    <Meldung>
      Du bist nicht angemeldet. <Link href="/konto/anmelden?weiter=/konto">Anmelden oder Konto anlegen</Link>
    </Meldung>
  );
}

function Gesperrt({ mitLoeschen = true }: { mitLoeschen?: boolean }) {
  return (
    <div className="konto-bereich">
      <Meldung art="fehler">{UNTER16}</Meldung>
      <AbmeldenKnoepfe />
      {mitLoeschen && <KontoLoeschen gesperrt />}
    </div>
  );
}

const antwortenAus = (p: Ich["praeferenzen"]): Antworten => ({
  kategorien: p.kategorien ?? [], unterkategorien: p.unterkategorien ?? [], stadtteile: p.stadtteile ?? [],
  merkmale: p.merkmale ?? [], orte: p.orte ?? [],
});

// ── /konto/willkommen ────────────────────────────────────────────────────────
export function WillkommenSeite({ daten }: { daten: FragebogenDaten }) {
  return (
    <Suspense fallback={null}>
      <Willkommen daten={daten} />
    </Suspense>
  );
}

function Willkommen({ daten }: { daten: FragebogenDaten }) {
  const router = useRouter();
  const modus = useSearchParams().get("modus") === "interessen" ? "interessen" : "onboarding";
  const [z, laden] = useIch();
  const [alter, setAlter] = useState(false);
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  if (z.art === "laden") return <div className="skeleton" style={{ height: 320 }} />;
  if (z.art === "abgemeldet") return <Abgemeldet />;
  if (z.art === "fehler") return <Meldung art="fehler">{z.text}</Meldung>;
  const ich = z.ich;
  if (ich.gesperrt) return <Gesperrt />;

  // Konto ohne Alters-Häkchen (am Formular vorbei angelegt): erst das Häkchen allein (Plan 5.3)
  if (!ich.mindestalter_bestaetigt) {
    return (
      <form
        className="formular konto-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setSendet(true);
          const a = await konto("einstellungen", "PUT", { art: "mindestalter", erteilt: true });
          setSendet(false);
          if (a.status === 200) {
            void uebernahmePruefen();
            await laden();
          } else setFehler(fehlerText(a));
        }}
      >
        <p>Bevor es weitergeht, bestätige bitte kurz dein Alter.</p>
        <label className="formular__check">
          <input type="checkbox" checked={alter} onChange={(e) => setAlter(e.target.checked)} required />
          <span>{TEXT.mindestalter}</span>
        </label>
        {fehler && <Meldung art="fehler">{fehler}</Meldung>}
        <div className="formular__aktionen">
          <button type="submit" className="btn btn--navy btn--gross" disabled={!alter || sendet}>Weiter</button>
        </div>
      </form>
    );
  }

  if (modus === "onboarding" && ich.onboarding_fertig_am) {
    return (
      <Meldung art="ok">
        Dein Profil ist fertig. <Link href="/konto">Zum Konto</Link> · <Link href="/merkliste">Zur Merkliste</Link>
      </Meldung>
    );
  }

  async function speichern(antworten: Antworten | null, werte: AbschlussWerte) {
    setSendet(true);
    setFehler(null);
    if (modus === "interessen") {
      const a = await konto("vorlieben", "PUT", {
        praeferenzen: { version: 1, ...(antworten ?? KEINE) },
        interessen_ok: ich.personalisierung ? true : werte.interessen_ok,
      });
      setSendet(false);
      if (a.status === 200) router.push("/konto");
      else setFehler(fehlerText(a));
      return;
    }
    const a = await konto("abschluss", "POST", {
      ...(antworten ? { praeferenzen: { version: 1, ...antworten } } : {}),
      interessen_ok: werte.interessen_ok,
      sensibel_ok: werte.sensibel_ok,
      widerspruch: werte.widerspruch,
      geburtstagsmail_ok: werte.geburtstagsmail_ok,
      vorname: werte.vorname,
      nachname: werte.nachname,
      geburtsdatum: werte.geburtsdatum,
      weiter: new URLSearchParams(window.location.search).get("weiter") ?? undefined,
    });
    setSendet(false);
    if (a.status === 200 && a.daten.gesperrt) {
      lokalAbmelden(true);
      await laden();
      return;
    }
    if (a.status === 200) {
      if (werte.sensibel_ok) await nurGeraetHochladen();
      router.push(typeof a.daten.ziel === "string" ? a.daten.ziel : "/merkliste");
      return;
    }
    setFehler(fehlerText(a));
  }

  return (
    <InteressenFragebogen
      daten={daten}
      start={modus === "interessen" ? antwortenAus(ich.praeferenzen) : KEINE}
      stammStart={{ vorname: ich.vorname ?? "", nachname: ich.nachname ?? "", geburtsdatum: ich.geburtsdatum ?? "" }}
      modus={modus}
      personalisierungGilt={ich.personalisierung}
      speichern={speichern}
      fehler={fehler}
      sendet={sendet}
    />
  );
}

// ── /konto ───────────────────────────────────────────────────────────────────
export function KontoSeite() {
  const [z, laden] = useIch();
  if (z.art === "laden") return <div className="skeleton" style={{ height: 320 }} />;
  if (z.art === "abgemeldet") return <Abgemeldet />;
  if (z.art === "fehler") return <Meldung art="fehler">{z.text}</Meldung>;
  const ich = z.ich;
  if (ich.gesperrt) return <Gesperrt />;

  return (
    <div className="konto-bereich">
      <section className="konto-abschnitt">
        <h2 className="d">Dein Konto</h2>
        <p>Deine Mailadresse: <b>{ich.email}</b></p>
        <p className="formular__hinweis">Adresse ändern? Schreib uns an <a href="mailto:moin@rocktician.com">moin@rocktician.com</a>.</p>
      </section>

      {!ich.mindestalter_bestaetigt || !ich.onboarding_fertig_am ? (
        <Meldung>
          Dein Profil ist noch nicht fertig. <Link href="/konto/willkommen">Jetzt abschließen</Link>
        </Meldung>
      ) : (
        <>
          <section className="konto-abschnitt">
            <h2 className="d">Deine Interessen</h2>
            <p>{interessenKurz(ich)}</p>
            <Link href="/konto/willkommen?modus=interessen" className="btn btn--outline btn--klein">Interessen ändern</Link>
          </section>
          <UeberDich ich={ich} neuLaden={laden} />
          <Einwilligungen ich={ich} neuLaden={laden} />
        </>
      )}

      <PasswortAendern />

      <section className="konto-abschnitt">
        <h2 className="d">Deine Daten</h2>
        <a href="/api/konto/export" className="btn btn--outline btn--klein" download>Deine Daten herunterladen</a>
        <p className="formular__hinweis">Eine vollständige Auskunft nach Art. 15 DSGVO bekommst du auch per Mail an moin@rocktician.com.</p>
      </section>

      <section className="konto-abschnitt">
        <h2 className="d">Abmelden</h2>
        <AbmeldenKnoepfe />
      </section>

      <KontoLoeschen />
    </div>
  );
}

function interessenKurz(ich: Ich): string {
  if (!ich.personalisierung) return "Keine Interessen gespeichert.";
  const p = ich.praeferenzen;
  const n = (p.kategorien?.length ?? 0) + (p.unterkategorien?.length ?? 0) + (p.stadtteile?.length ?? 0) + (p.merkmale?.length ?? 0) + (p.orte?.length ?? 0);
  return n ? `${n} Angaben gespeichert.` : "Gespeichert: keine besonderen Vorlieben.";
}

function Einwilligungen({ ich, neuLaden }: { ich: Ich; neuLaden: () => Promise<void> }) {
  const [fehler, setFehler] = useState<string | null>(null);
  const [sendet, setSendet] = useState(false);

  async function setzen(body: Record<string, unknown>) {
    setSendet(true);
    setFehler(null);
    const a = await konto("einstellungen", "PUT", body);
    setSendet(false);
    if (a.status !== 200) return setFehler(fehlerText(a));
    if (Array.isArray(a.daten.zurueck_aufs_geraet)) zurueckAufsGeraet(a.daten.zurueck_aufs_geraet as string[]);
    if (body.art === "sensible_events" && body.erteilt === true) await nurGeraetHochladen();
    if (a.daten.gesperrt) lokalAbmelden(true);
    await neuLaden();
  }

  return (
    <section className="konto-abschnitt">
      <h2 className="d">Deine Einwilligungen</h2>
      <label className="formular__check">
        <input type="checkbox" checked={ich.personalisierung} disabled={sendet}
          onChange={(e) => setzen({ art: "personalisierung", erteilt: e.target.checked })} />
        <span><b>Interessen speichern und Empfehlungen.</b> {TEXT.personalisierung}</span>
      </label>
      <label className="formular__check">
        <input type="checkbox" checked={ich.sensible_events_erlaubt} disabled={sendet}
          onChange={(e) => {
            if (!e.target.checked && !window.confirm(TEXT.widerrufSensibel)) return;
            void setzen({ art: "sensible_events", erteilt: e.target.checked });
          }} />
        <span><b>Sensible Events im Konto speichern.</b> {TEXT.sensibelErklaerung} {TEXT.sensibel}</span>
      </label>
      <label className="formular__check">
        <input type="checkbox" checked={ich.widerspruch_zaehlung} disabled={sendet}
          onChange={(e) => setzen({ art: "analyse", erteilt: !e.target.checked })} />
        <span><b>Meine Merkliste nicht anonym mitzählen.</b> {TEXT.widerspruchErklaerung}</span>
      </label>
      <label className="formular__check">
        <input type="checkbox" checked={ich.geburtstagsmail} disabled={sendet || !ich.geburtsdatum}
          onChange={(e) => setzen({ art: "geburtstagsmail", erteilt: e.target.checked })} />
        <span><b>Geburtstagsmail.</b> {TEXT.geburtstag}</span>
      </label>
      {fehler && <Meldung art="fehler">{fehler}</Meldung>}
    </section>
  );
}

/** Name und Geburtsdatum (E16): Pflichtangaben, hier änderbar. Ein Datum unter 16 sperrt das Konto. */
function UeberDich({ ich, neuLaden }: { ich: Ich; neuLaden: () => Promise<void> }) {
  const [w, setW] = useState({ vorname: ich.vorname ?? "", nachname: ich.nachname ?? "", geburtsdatum: ich.geburtsdatum ?? "" });
  const [fehler, setFehler] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const [sendet, setSendet] = useState(false);
  const geaendert = w.vorname !== (ich.vorname ?? "") || w.nachname !== (ich.nachname ?? "") || w.geburtsdatum !== (ich.geburtsdatum ?? "");

  return (
    <section className="konto-abschnitt">
      <h2 className="d">Über dich</h2>
      <form
        className="formular"
        onSubmit={async (e) => {
          e.preventDefault();
          setSendet(true);
          setFehler(null);
          setOk(false);
          const a = await konto("stammdaten", "PUT", w);
          setSendet(false);
          if (a.status !== 200) return setFehler(fehlerText(a));
          if (a.daten.gesperrt) lokalAbmelden(true);
          else setOk(true);
          await neuLaden();
        }}
      >
        <div className="konto-stamm">
          <div className="formular__feld">
            <label className="formular__label" htmlFor="konto-vorname">Vorname</label>
            <input id="konto-vorname" type="text" autoComplete="given-name" maxLength={60} required value={w.vorname}
              onChange={(e) => setW({ ...w, vorname: e.target.value })} />
          </div>
          <div className="formular__feld">
            <label className="formular__label" htmlFor="konto-nachname">Nachname</label>
            <input id="konto-nachname" type="text" autoComplete="family-name" maxLength={60} required value={w.nachname}
              onChange={(e) => setW({ ...w, nachname: e.target.value })} />
          </div>
        </div>
        <div className="formular__feld">
          <label className="formular__label" htmlFor="konto-geburtsdatum">Geburtsdatum</label>
          <input id="konto-geburtsdatum" type="date" autoComplete="bday" min="1900-01-01" required value={w.geburtsdatum}
            onChange={(e) => setW({ ...w, geburtsdatum: e.target.value })} />
        </div>
        <p className="formular__hinweis">{TEXT.stammdaten.text}</p>
        {fehler && <Meldung art="fehler">{fehler}</Meldung>}
        {ok && !geaendert && <Meldung art="ok">Gespeichert.</Meldung>}
        {geaendert && (
          <div className="formular__aktionen">
            <button type="submit" className="btn btn--outline btn--klein" disabled={sendet}>Speichern</button>
          </div>
        )}
      </form>
    </section>
  );
}

function PasswortAendern() {
  const [offen, setOffen] = useState(false);
  const [aktuell, setAktuell] = useState("");
  const [neu, setNeu] = useState("");
  const [text, setText] = useState<{ art: "ok" | "fehler"; t: string } | null>(null);
  const [sendet, setSendet] = useState(false);
  return (
    <section className="konto-abschnitt">
      <h2 className="d">Passwort</h2>
      {!offen ? (
        <button type="button" className="btn btn--outline btn--klein" onClick={() => setOffen(true)}>Passwort ändern</button>
      ) : (
        <form
          className="formular"
          onSubmit={async (e) => {
            e.preventDefault();
            setSendet(true);
            const a = await konto("passwort-aendern", "POST", { aktuell, neu });
            setSendet(false);
            setAktuell("");
            setNeu("");
            setText(a.status === 200 ? { art: "ok", t: String(a.daten.meldung) } : { art: "fehler", t: fehlerText(a) });
            if (a.status === 200) setOffen(false);
          }}
        >
          <PasswortFeld id="pw-aktuell" label="Aktuelles Passwort" wert={aktuell} setzen={setAktuell} autocomplete="current-password" />
          <PasswortFeld id="pw-neu" label="Neues Passwort" wert={neu} setzen={setNeu} autocomplete="new-password" hinweis="Mindestens 10 Zeichen." />
          <div className="formular__aktionen">
            <button type="submit" className="btn btn--navy" disabled={sendet}>Speichern</button>
            <button type="button" className="link konto-textknopf" onClick={() => setOffen(false)}>Abbrechen</button>
          </div>
        </form>
      )}
      {text && <Meldung art={text.art}>{text.t}</Meldung>}
    </section>
  );
}

function AbmeldenKnoepfe() {
  const router = useRouter();
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState(false);
  const knopf = async (ueberall: boolean) => {
    setSendet(true);
    setFehler(false);
    // Erst Warteschlange senden, dann Server abmelden; lokal nur nach Bestätigung (Plan 5.6)
    const ok = await abmelden(ueberall);
    setSendet(false);
    if (!ok) return setFehler(true);
    router.push("/merkliste");
    router.refresh();
  };
  return (
    <>
      <div className="formular__aktionen">
        <button type="button" className="btn btn--outline btn--klein" disabled={sendet} onClick={() => knopf(false)}>Auf diesem Gerät abmelden</button>
        <button type="button" className="btn btn--outline btn--klein" disabled={sendet} onClick={() => knopf(true)}>Überall abmelden</button>
      </div>
      {fehler && <Meldung art="fehler">Abmelden hat nicht geklappt. Bitte prüf deine Verbindung und versuch es noch einmal.</Meldung>}
    </>
  );
}

function KontoLoeschen({ gesperrt = false }: { gesperrt?: boolean }) {
  const [offen, setOffen] = useState(false);
  const [passwort, setPasswort] = useState("");
  const [wort, setWort] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [fertig, setFertig] = useState<string | null>(null);
  const [sendet, setSendet] = useState(false);
  if (fertig) return <Meldung art="ok">{fertig}</Meldung>;
  return (
    <section className="konto-abschnitt">
      <h2 className="d">Konto löschen</h2>
      {!offen ? (
        <button type="button" className="btn btn--outline btn--klein" onClick={() => setOffen(true)}>Konto löschen …</button>
      ) : (
        <form
          className="formular"
          onSubmit={async (e) => {
            e.preventDefault();
            setSendet(true);
            const a = await konto("loeschen", "POST", { passwort, bestaetigung: wort });
            setSendet(false);
            setPasswort("");
            if (a.status === 200) {
              lokalAbmelden();
              setFertig(String(a.daten.meldung));
            } else setFehler(fehlerText(a));
          }}
        >
          <p>{gesperrt ? "Du kannst dein Konto auch sofort selbst löschen." : "Dein Konto und deine Merkliste werden endgültig gelöscht."}</p>
          <PasswortFeld id="loeschen-pw" label="Aktuelles Passwort" wert={passwort} setzen={setPasswort} autocomplete="current-password" />
          <div className="formular__feld">
            <label className="formular__label" htmlFor="loeschen-wort">Tippe LÖSCHEN zur Bestätigung</label>
            <input id="loeschen-wort" value={wort} onChange={(e) => setWort(e.target.value)} autoComplete="off" />
          </div>
          {fehler && <Meldung art="fehler">{fehler}</Meldung>}
          <div className="formular__aktionen">
            <button type="submit" className="btn btn--navy" disabled={sendet || wort !== "LÖSCHEN" || !passwort}>Endgültig löschen</button>
            <button type="button" className="link konto-textknopf" onClick={() => setOffen(false)}>Abbrechen</button>
          </div>
        </form>
      )}
    </section>
  );
}
