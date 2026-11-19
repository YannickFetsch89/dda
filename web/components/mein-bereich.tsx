"use client";
// Mein dies.das (Plan Mein Bereich 3.1, 3.3, 3.5): Übersicht /konto, /konto/fuer-dich und /konto/erlebt.
// Statische Hüllen; alles Persönliche kommt per Client-Abruf aus /api/konto/* (private, no-store).
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMerkliste } from "./client";
import { EventKarte, Leer, SkeletonKarten } from "./karten";
import { Meldung, fehlerText, konto, type Antwort } from "./konto";
import { KontoHuelle, ProfilHinweis, profilFertig, type Ich } from "./konto-bereich";
import { abgleichen, kontomodus, lokalAbmelden } from "@/lib/konto/merk-store";
import { merklisteAufteilen } from "@/lib/konto/merk-logik";
import type { DddEvent } from "@/lib/typen";

type Abruf<T> = { art: "laden" } | { art: "fehler"; text: string } | { art: "abgemeldet" } | ({ art: "da" } & T);

/**
 * Gemeinsame Antwort-Behandlung der neuen Abrufe (Plan 3.0): 401 → lokal abmelden; 403 mindestalter_fehlt → lokal
 * abmelden mit Alters-Hinweis (data-konto="0"); 403 passwort_setzen_noetig → /konto/passwort-neu. Kein Wiederholen.
 */
function useKontoAbruf<T>(pfad: string | null, auswerten: (a: Antwort) => T): Abruf<T> {
  const router = useRouter();
  const [z, setZ] = useState<Abruf<T>>({ art: "laden" });
  useEffect(() => {
    if (!pfad) return;
    let abgebrochen = false;
    void konto(pfad).then((a) => {
      if (abgebrochen) return;
      if (a.status === 401) {
        lokalAbmelden();
        setZ({ art: "abgemeldet" });
      } else if (a.status === 403 && a.daten.code === "passwort_setzen_noetig") {
        router.push("/konto/passwort-neu");
      } else if (a.status === 403 && a.daten.code === "mindestalter_fehlt") {
        lokalAbmelden(true);
        setZ({ art: "fehler", text: "Bestätige kurz dein Alter, dann geht es hier weiter." });
      } else if (a.status === 200) {
        setZ({ art: "da", ...auswerten(a) });
      } else setZ({ art: "fehler", text: fehlerText(a) });
    });
    return () => {
      abgebrochen = true;
    };
    // auswerten ist je Seite eine feste Funktion; neu laden nur bei anderem Pfad
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pfad, router]);
  return z;
}

// ── /konto (Übersicht, Plan 3.1) ─────────────────────────────────────────────
interface Zahlen {
  vorschlaege: number | null;
  unbekannt: boolean;
  kommende: number;
  erlebt: number;
  interessen: number;
  /** Events der Merkliste nicht geladen: kommende/erlebt wären 0, obwohl es Merkungen gibt (Cursor-Befund 3) */
  merklisteUnvollstaendig: boolean;
}
const zahlenAus = (a: Antwort): Zahlen => ({
  vorschlaege: typeof a.daten.vorschlaege === "number" ? a.daten.vorschlaege : null,
  unbekannt: a.daten.vorschlaege_unbekannt === true,
  merklisteUnvollstaendig: a.daten.merkliste_unvollstaendig === true,
  kommende: Number(a.daten.kommende) || 0,
  erlebt: Number(a.daten.erlebt) || 0,
  interessen: Number(a.daten.interessen) || 0,
});

const merkWert = (zahlen: Zahlen | null, feld: "kommende" | "erlebt"): string | null =>
  !zahlen ? null : zahlen.merklisteUnvollstaendig ? "Ansehen" : String(zahlen[feld]);

export function UebersichtSeite() {
  return <KontoHuelle>{(ich) => <Uebersicht ich={ich} />}</KontoHuelle>;
}

function Uebersicht({ ich }: { ich: Ich }) {
  // Die Zahlen brauchen das Alters-Häkchen; ohne bleibt es beim Hinweis und den Links
  const z = useKontoAbruf(ich.mindestalter_bestaetigt ? "uebersicht" : null, zahlenAus);
  const zahlen = z.art === "da" ? z : null;
  const laedt = ich.mindestalter_bestaetigt && z.art === "laden";

  let fuerDich: string | null = null;
  let fuerDichZiel = "/konto/fuer-dich";
  if (zahlen) {
    if (zahlen.unbekannt) fuerDich = "Ansehen";
    else if (zahlen.vorschlaege === null) {
      fuerDich = "Interessen angeben";
      fuerDichZiel = "/konto/interessen";
    } else fuerDich = String(zahlen.vorschlaege);
  }

  return (
    <div className="konto-bereich">
      <p className="konto-mail">{ich.email}</p>
      {!profilFertig(ich) && <ProfilHinweis />}
      {z.art === "fehler" && <Meldung art="fehler">{z.text}</Meldung>}

      <section aria-labelledby="gruppe-fuer-mich">
        <h2 className="konto-gruppe" id="gruppe-fuer-mich">Für mich</h2>
        <ul className="konto-kacheln">
          <Kachel href={fuerDichZiel} icon="auto_awesome" name="Für dich" wert={fuerDich} laedt={laedt} />
          {/* Bei unvollständiger Merkliste keine Zahl, nur „Ansehen“ (wie bei vorschlaege_unbekannt) */}
          <Kachel href="/merkliste" icon="favorite" name="Merkliste" wert={merkWert(zahlen, "kommende")} laedt={laedt} />
          <Kachel href="/konto/erlebt" icon="history" name="Erlebt" wert={merkWert(zahlen, "erlebt")} laedt={laedt} />
          <Kachel
            href="/konto/interessen" icon="interests" name="Interessen" laedt={laedt}
            wert={zahlen ? (zahlen.interessen ? String(zahlen.interessen) : "Noch keine") : null}
          />
        </ul>
      </section>

      <section aria-labelledby="gruppe-konto">
        <h2 className="konto-gruppe" id="gruppe-konto">Konto</h2>
        <ul className="konto-liste">
          <li>
            <Link href="/konto/einstellungen">
              <span className="icon" aria-hidden data-icon="shield_person" />
              <span>
                <b>Konto und Sicherheit</b>
                <small>Name und Geburtsdatum, Mailadresse, Passwort, Abmelden, Löschen</small>
              </span>
              <span className="icon konto-liste__pfeil" aria-hidden data-icon="chevron_right" />
            </Link>
          </li>
          <li>
            <Link href="/konto/datenschutz">
              <span className="icon" aria-hidden data-icon="privacy_tip" />
              <span>
                <b>Datenschutz</b>
                <small>Einwilligungen und Auskunft über deine Daten</small>
              </span>
              <span className="icon konto-liste__pfeil" aria-hidden data-icon="chevron_right" />
            </Link>
          </li>
        </ul>
      </section>
    </div>
  );
}

function Kachel({ href, icon, name, wert, laedt }: { href: string; icon: string; name: string; wert: string | null; laedt: boolean }) {
  // Zahl oder kurzer Text; reine Zahlen groß, Wörter („Ansehen“, „Noch keine“) kleiner
  const istZahl = wert !== null && /^\d+$/.test(wert);
  return (
    <li>
      <Link href={href} className="konto-kachel">
        <span className="icon" aria-hidden data-icon={icon} />
        <span className="konto-kachel__name">{name}</span>
        {laedt ? (
          <span className="konto-kachel__wert skeleton" aria-hidden />
        ) : (
          wert !== null && <span className={`konto-kachel__wert${istZahl ? "" : " konto-kachel__wert--text"}`}>{wert}</span>
        )}
      </Link>
    </li>
  );
}

// ── /konto/fuer-dich (Plan 3.3) ──────────────────────────────────────────────
type Abschnitt = { schluessel: string; titel: string; events: (DddEvent & { begruendung?: string })[] };
const fuerDichAus = (a: Antwort) => ({
  personalisierung: a.daten.personalisierung === true,
  heute: typeof a.daten.heute === "string" ? a.daten.heute : "",
  abschnitte: Array.isArray(a.daten.abschnitte) ? (a.daten.abschnitte as Abschnitt[]) : [],
});

export function FuerDichSeite() {
  return <KontoHuelle>{(ich) => (ich.mindestalter_bestaetigt ? <FuerDich /> : <ProfilHinweis />)}</KontoHuelle>;
}

function FuerDich() {
  const z = useKontoAbruf("fuer-dich", fuerDichAus);
  if (z.art === "laden") return <SkeletonKarten anzahl={6} />;
  if (z.art === "abgemeldet") return <Meldung>Du bist nicht angemeldet. <Link href="/konto/anmelden?weiter=/konto/fuer-dich">Anmelden</Link></Meldung>;
  if (z.art === "fehler") return <Meldung art="fehler">{z.text}</Meldung>;
  if (!z.personalisierung) {
    return (
      <Leer titel="Für Vorschläge brauchen wir deine Interessen">
        <Link href="/konto/interessen" className="btn btn--gold">Interessen angeben</Link>
      </Leer>
    );
  }
  // Leer trotz Einwilligung: kein Grund, keine Zahl, kein Hinweis auf die Merkliste (Plan 3.3, 8)
  if (!z.abschnitte.length) {
    return (
      <Leer titel="Im Moment haben wir keine Vorschläge für dich.">
        <Link href="/konto/interessen" className="btn btn--outline">Interessen ansehen</Link>
      </Leer>
    );
  }
  return (
    <div className="fuer-dich">
      {z.abschnitte.map((a) => (
        <section key={a.schluessel} className="fuer-dich__abschnitt" aria-labelledby={`fd-${a.schluessel}`}>
          <h2 className="d" id={`fd-${a.schluessel}`}>{a.titel}</h2>
          <div className="raster" role="list">
            {a.events.map((e) => <EventKarte key={e.id} e={e} heute={z.heute} variante="grid" grund={e.begruendung} />)}
          </div>
        </section>
      ))}
    </div>
  );
}

// ── /konto/erlebt (Plan 3.5) ─────────────────────────────────────────────────
const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
const ende = (e: DddEvent) => e.datum_bis ?? e.datum;
const monatsName = (iso: string) => `${MONATE[Number(iso.slice(5, 7)) - 1] ?? ""} ${iso.slice(0, 4)}`;

const erlebtAus = (a: Antwort) => ({
  heute: typeof a.daten.heute === "string" ? a.daten.heute : "",
  events: Array.isArray(a.daten.events) ? (a.daten.events as DddEvent[]) : [],
  eventsFehler: typeof a.daten.fehler === "string",
});

export function ErlebtSeite() {
  return <KontoHuelle>{(ich) => (ich.mindestalter_bestaetigt ? <Erlebt /> : <ProfilHinweis />)}</KontoHuelle>;
}

function Erlebt() {
  const z = useKontoAbruf("merkliste?mit=events", erlebtAus);
  const ids = useMerkliste();
  // Wie die Merkliste: beim Öffnen mit dem Konto abgleichen, damit das Herz hier dieselbe Liste sieht
  useEffect(() => {
    if (kontomodus()) void abgleichen();
  }, []);

  if (z.art === "laden") return <SkeletonKarten anzahl={6} />;
  if (z.art === "abgemeldet") return <Meldung>Du bist nicht angemeldet. <Link href="/konto/anmelden?weiter=/konto/erlebt">Anmelden</Link></Meldung>;
  if (z.art === "fehler") return <Meldung art="fehler">{z.text}</Meldung>;
  if (z.eventsFehler) return <Meldung art="fehler">Die Events konnten gerade nicht geladen werden. Bitte versuch es gleich noch einmal.</Meldung>;

  // Herz entfernt → Eintrag verschwindet sofort (lokale Liste), gelöscht wird im Konto wie auf der Merkliste
  const { vorbei } = merklisteAufteilen(z.events.filter((e) => ids.includes(e.id)), z.heute);
  if (!vorbei.length) {
    return (
      <Leer titel="Noch nichts erlebt.">
        <span>Hier landen deine gemerkten Events, sobald sie vorbei sind.</span>
        <Link href="/merkliste" className="link">Zur Merkliste</Link>
      </Leer>
    );
  }
  const sortiert = [...vorbei].sort((a, b) => ende(b).localeCompare(ende(a)) || b.datum.localeCompare(a.datum));
  const gruppen: { monat: string; events: DddEvent[] }[] = [];
  for (const e of sortiert) {
    const monat = ende(e).slice(0, 7);
    const letzte = gruppen[gruppen.length - 1];
    if (letzte?.monat === monat) letzte.events.push(e);
    else gruppen.push({ monat, events: [e] });
  }
  return (
    <div className="fuer-dich">
      {gruppen.map((g) => (
        <section key={g.monat} className="fuer-dich__abschnitt" aria-labelledby={`erlebt-${g.monat}`}>
          <h2 className="d" id={`erlebt-${g.monat}`}>{monatsName(`${g.monat}-01`)}</h2>
          <div className="raster" role="list">
            {g.events.map((e) => <EventKarte key={e.id} e={e} heute={z.heute} variante="grid" />)}
          </div>
        </section>
      ))}
    </div>
  );
}
