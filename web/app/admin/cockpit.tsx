"use client";
// Cockpit: Ampeln, Warnungen der Scraper-Läufe, „Zu erledigen“ und Kennzahlen. Daten aus /api/admin/cockpit.
import { useCallback, useEffect, useState } from "react";
import type { CockpitDaten } from "@/lib/admin/cockpit";

const FARBE_TEXT = { gruen: "in Ordnung", gelb: "Achtung", rot: "Problem", grau: "unbekannt" } as const;

function zeit(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  // Reine Datumsangaben (YYYY-MM-DD) ohne Uhrzeit
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
  return d.toLocaleString("de-DE", { timeZone: "Europe/Berlin", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function zahl(n: number | null): string {
  return n === null ? "–" : n.toLocaleString("de-DE");
}

export function Cockpit() {
  const [daten, setDaten] = useState<CockpitDaten | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laedt, setLaedt] = useState(false);

  const laden = useCallback(async () => {
    setLaedt(true);
    try {
      const r = await fetch("/api/admin/cockpit", { cache: "no-store" });
      if (r.status === 401) return window.location.assign("/admin/anmelden");
      const d = (await r.json()) as CockpitDaten & { fehler?: string; code?: string };
      if (r.status === 403 && d.code === "zwei_faktor") return window.location.assign("/admin/zwei-faktor");
      if (!r.ok) throw new Error(d.fehler ?? `Fehler ${r.status}`);
      setDaten(d);
      setFehler(null);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Cockpit konnte nicht geladen werden.");
    }
    setLaedt(false);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden beim Öffnen
    laden();
  }, [laden]);

  return (
    <>
      <div className="admin-kopfzeile">
        <div>
          <h1>Cockpit</h1>
          <p className="admin-unterzeile">{daten ? `Stand ${zeit(daten.jetzt)}` : "Wird geladen …"}</p>
        </div>
        <button type="button" className="admin-knopf admin-knopf--leise" onClick={laden} disabled={laedt}>
          {laedt ? "Lädt …" : "Neu laden"}
        </button>
      </div>
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}

      {daten && (
        <>
          <section aria-label="Kennzahlen" className="admin-kennzahlen">
            <div><strong>{zahl(daten.kennzahlen.eventsHeute)}</strong><span>Events heute</span></div>
            <div><strong>{zahl(daten.kennzahlen.events7Tage)}</strong><span>nächste 7 Tage</span></div>
            <div><strong>{zahl(daten.kennzahlen.neuSeitLauf)}</strong><span>neu seit letztem Lauf</span></div>
            <div><strong>{zahl(daten.kennzahlen.konten)}</strong><span>Konten</span></div>
          </section>

          <h2 className="admin-abschnitt">Ampeln</h2>
          <ul className="admin-ampeln">
            {daten.ampeln.map((a) => (
              <li key={a.schluessel} className={`admin-ampel admin-ampel--${a.farbe}`}>
                <span className="admin-punkt" aria-label={FARBE_TEXT[a.farbe]} />
                <div>
                  <strong>{a.titel}</strong>
                  <span>{a.text}</span>
                  {a.zeitpunkt && <small>{zeit(a.zeitpunkt)}</small>}
                </div>
                {a.link && (
                  <a href={a.link} target="_blank" rel="noreferrer noopener">
                    öffnen
                  </a>
                )}
              </li>
            ))}
          </ul>

          {daten.warnungen.length > 0 && (
            <>
              <h2 className="admin-abschnitt">Warnungen aus dem Scraper-Lauf</h2>
              <ul className="admin-liste">
                {daten.warnungen.map((w, i) => (
                  <li key={`${w.regel}-${w.quelle}-${i}`} className={`admin-liste__eintrag admin-liste__eintrag--${w.stufe}`}>
                    <span className="admin-marke-klein">{w.regel}</span>
                    <strong>{w.quelle ?? "Lauf"}</strong>
                    <span>{w.text}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          <h2 className="admin-abschnitt">Zu erledigen</h2>
          <ul className="admin-liste">
            {daten.aufgaben.map((a) => (
              <li key={a.schluessel} className={`admin-liste__eintrag admin-liste__eintrag--${a.farbe}`}>
                <span className="admin-zahl">{zahl(a.anzahl)}</span>
                <strong>{a.link ? <a href={a.link}>{a.titel}</a> : a.titel}</strong>
                {a.hinweis && <span>{a.hinweis}</span>}
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}
