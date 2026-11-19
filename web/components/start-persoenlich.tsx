"use client";
// Startseite angemeldet (Plan Mein Bereich 4.1, 4.2): Insel „Für dich empfohlen“ und „Deine nächsten Events“.
// Lädt nur bei html[data-konto="1"], einmal je Datum (useSearchParams, eigene Suspense-Grenze in page.tsx).
// Keine Wiederholung desselben Fehlschlags; 429/5xx/keine Verbindung klappen das Modul still zu.
// Außerdem die Links der Vorschau B18 (4.3), die `weiter` auf die aktuelle Start-URL setzen.
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Reihe, useKontoZustand } from "./client";
import { EventKarte, KompaktKarte } from "./karten";
import { konto } from "./konto";
import { lokalAbmelden } from "@/lib/konto/merk-store";
import type { DddEvent } from "@/lib/typen";

type Vorschlag = DddEvent & { begruendung?: string };
type Daten = {
  personalisierung: boolean;
  ersatz: boolean;
  heute: string;
  fuer_dich: Vorschlag[];
  naechste: DddEvent[];
  vorname?: string;
};
type Zustand = { art: "laden" } | { art: "weg" } | { art: "reset" } | { art: "da"; d: Daten };

/** Höchstens so viele gezeigte Tipp-und-Picks-IDs gehen als `ohne` mit (Tipp + 4 Picks) */
const OHNE_MAX = 5;

/** IDs der sichtbaren Tipp-und-Picks-Karten, eindeutig (mobil und Desktop stehen beide im HTML). Keine Geräte-IDs. */
function gezeigteIds(): string[] {
  const ids = new Set<string>();
  document.querySelectorAll<HTMLElement>("[data-start-gezeigt] [data-event-id]").forEach((el) => {
    const id = el.dataset.eventId;
    if (id && ids.size < OHNE_MAX) ids.add(id);
  });
  return [...ids];
}

export function StartPersoenlich() {
  const zustand = useKontoZustand();
  const datum = useSearchParams().get("datum") ?? "";
  // Abgemeldet und Cookie 0: nichts laden. Der Platzhalter steht trotzdem im Server-HTML (Server-Momentaufnahme ist
  // abgemeldet); CSS zeigt ihn nur bei html[data-konto="1"], so hält er vor der Hydration die Höhe frei (4.1)
  if (zustand !== "1") return <div className="start-platzhalter" aria-hidden />;
  // key: neues Datum → neuer Abruf; derselbe Fehlschlag wird nicht wiederholt
  return <StartModule key={datum} datum={datum} />;
}

function StartModule({ datum }: { datum: string }) {
  const [z, setZ] = useState<Zustand>({ art: "laden" });
  useEffect(() => {
    let abgebrochen = false;
    const q = new URLSearchParams();
    if (datum) q.set("datum", datum);
    const ohne = gezeigteIds();
    if (ohne.length) q.set("ohne", ohne.join(","));
    void konto(`start${q.size ? `?${q}` : ""}`).then((a) => {
      if (abgebrochen) return;
      if (a.status === 200) setZ({ art: "da", d: a.daten as unknown as Daten });
      else if (a.status === 401) {
        // Sitzung weg: lokal abmelden → Attribut fällt weg → Vorschau erscheint, die Insel rendert nichts mehr
        lokalAbmelden();
        setZ({ art: "weg" });
      } else if (a.status === 403 && a.daten.code === "mindestalter_fehlt") {
        lokalAbmelden(true);
        setZ({ art: "weg" });
      } else if (a.status === 403 && a.daten.code === "passwort_setzen_noetig") {
        // Reset-Sitzung mit altem Cookie 1: Hinweis, kein Abmelden, keine Vorschau, kein erneuter Abruf
        setZ({ art: "reset" });
      } else setZ({ art: "weg" });
    });
    return () => {
      abgebrochen = true;
    };
  }, [datum]);

  if (z.art === "laden") return <div className="start-platzhalter start-platzhalter--laedt" aria-hidden />;
  if (z.art === "weg") return null;
  if (z.art === "reset") {
    return (
      <section className="sektion start-modul">
        <div className="status status--info" role="status">
          <span className="icon" aria-hidden data-icon="info" />
          <div>
            Bitte leg zuerst ein neues Passwort fest. <Link href="/konto/passwort-neu">Neues Passwort festlegen</Link>
          </div>
        </div>
      </section>
    );
  }
  const { d } = z;
  return (
    <>
      <FuerDichModul d={d} />
      {d.naechste.length > 0 && (
        <section className="sektion start-modul" aria-labelledby="start-naechste">
          <div className="sektionskopf sektionskopf--stapeln">
            <h2 className="d" id="start-naechste">Deine nächsten Events</h2>
            <Link href="/merkliste">Zur Merkliste</Link>
          </div>
          <div className="start-naechste" role="list">
            {d.naechste.map((e) => <KompaktKarte key={e.id} e={e} heute={d.heute} />)}
          </div>
        </section>
      )}
    </>
  );
}

function FuerDichModul({ d }: { d: Daten }) {
  const gruss = d.vorname ? <span className="start-modul__gruss">Hallo {d.vorname}</span> : null;
  // Ohne Einwilligung (a): schmale Zeile mit Button, keine Punkte, kein Ersatz
  if (!d.personalisierung) {
    return (
      <section className="sektion start-modul" aria-label="Für dich empfohlen">
        <div className="start-interessen">
          <span className="icon" aria-hidden data-icon="auto_awesome" />
          <p>Gib deine Interessen an und bekomme hier passende Vorschläge.</p>
          <Link href="/konto/interessen" className="btn btn--gold btn--klein">Interessen angeben</Link>
        </div>
      </section>
    );
  }
  // Vergangener Tag oder keine Kandidaten: Modul klappt still zu
  if (!d.fuer_dich.length) return null;
  const titel = d.ersatz ? "Beliebt in Düsseldorf" : "Für dich empfohlen";
  return (
    <section className="sektion start-modul" aria-labelledby="start-fuer-dich">
      <div className="sektionskopf sektionskopf--stapeln">
        <div>
          <h2 className="d" id="start-fuer-dich">{titel}</h2>
          {gruss}
        </div>
        {!d.ersatz && <Link href="/konto/fuer-dich">Alle Vorschläge</Link>}
      </div>
      <Reihe breite={220} label={titel}>
        {d.fuer_dich.map((e) => <EventKarte key={e.id} e={e} heute={d.heute} grund={d.ersatz ? undefined : e.begruendung} />)}
      </Reihe>
    </section>
  );
}

/** Button und Link der Vorschau B18; `weiter` ist die aktuelle Start-URL (/ oder /?datum=…), ohne Personenbezug */
export function VorschauLinks() {
  const datum = useSearchParams().get("datum");
  return <VorschauLinksMit weiter={datum ? `/?datum=${datum}` : "/"} />;
}

/** Ohne Suspense-Auflösung (Vorrendern): weiter=/. Einmal kodiert, Schrägstriche lesbar wie bei weiter=/merkliste */
export function VorschauLinksMit({ weiter }: { weiter: string }) {
  const w = encodeURIComponent(weiter).replace(/%2F/gi, "/");
  return (
    <>
      <Link href={`/konto/anmelden?neu=1&weiter=${w}`} className="btn btn--gold">Kostenlos registrieren</Link>
      <Link href={`/konto/anmelden?weiter=${w}`} className="link">Schon ein Konto? Anmelden</Link>
    </>
  );
}

