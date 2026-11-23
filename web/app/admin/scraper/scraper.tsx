"use client";
// Scraper-Seite: Lauf starten, Läufe, Quellen mit Verlauf der letzten 10 Läufe und Warnungen W1–W6.
import { useCallback, useEffect, useState } from "react";
import type { ScraperDaten } from "@/lib/admin/scraper";

const STATUS_LAUF = { laeuft: "läuft", erfolgreich: "erfolgreich", fehler: "abgebrochen" } as const;
const STATUS_QUELLE = { ok: "ok", leer: "leer", saisonal: "Saisonpause", uebersprungen: "übersprungen", fehler: "Fehler" } as const;
const KOPF = { "Content-Type": "application/json" };

function zeit(iso: string | null): string {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("de-DE", { timeZone: "Europe/Berlin", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function dauer(von: string, bis: string | null): string {
  if (!bis) return "–";
  const min = Math.round((new Date(bis).getTime() - new Date(von).getTime()) / 60000);
  return `${min} min`;
}

export function ScraperSeite() {
  const [daten, setDaten] = useState<ScraperDaten | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [hinweis, setHinweis] = useState<string | null>(null);
  const [startet, setStartet] = useState(false);

  const laden = useCallback(async () => {
    try {
      const r = await fetch("/api/admin/scraper", { cache: "no-store" });
      if (r.status === 401) return window.location.assign("/admin/anmelden");
      const d = (await r.json()) as ScraperDaten & { fehler?: string; code?: string };
      if (r.status === 403 && d.code === "zwei_faktor") return window.location.assign("/admin/zwei-faktor");
      if (!r.ok) throw new Error(d.fehler ?? `Fehler ${r.status}`);
      setDaten(d);
      setFehler(null);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Daten konnten nicht geladen werden.");
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden beim Öffnen
    laden();
  }, [laden]);

  async function starten() {
    if (!window.confirm("Scraper-Lauf jetzt starten? Er dauert etwa 30–60 Minuten.")) return;
    setStartet(true);
    setHinweis(null);
    try {
      const r = await fetch("/api/admin/scraper/starten", { method: "POST", headers: KOPF, body: "{}" });
      const d = (await r.json().catch(() => ({}))) as { fehler?: string };
      setHinweis(r.ok ? "Lauf gestartet. Er erscheint in wenigen Minuten unten in der Liste." : (d.fehler ?? "Start hat nicht geklappt."));
    } catch {
      setHinweis("Keine Verbindung. Bitte noch einmal versuchen.");
    }
    setStartet(false);
  }

  const gh = daten?.github;
  const ghLauf = gh?.art === "ok" ? gh.lauf : null;

  return (
    <>
      <div className="admin-kopfzeile">
        <div>
          <h1>Scraper</h1>
          <p className="admin-unterzeile">
            Rhythmus alle 3 Tage, 05:00 UTC.
            {ghLauf && (
              <>
                {" "}Letzter GitHub-Lauf {zeit(ghLauf.erstellt_am)}:{" "}
                <a href={ghLauf.url} target="_blank" rel="noreferrer noopener">
                  {ghLauf.status === "completed" ? (ghLauf.conclusion ?? "beendet") : "läuft"}
                </a>
              </>
            )}
          </p>
        </div>
        <button type="button" className="admin-knopf" onClick={starten} disabled={startet}>
          {startet ? "Startet …" : "Lauf starten"}
        </button>
      </div>
      {hinweis && <p className="admin-karte" role="status">{hinweis}</p>}
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}
      {!daten && !fehler && <p className="admin-unterzeile">Wird geladen …</p>}

      {daten && (
        <>
          {daten.laufWarnungen.length > 0 && (
            <ul className="admin-liste">
              {daten.laufWarnungen.map((w) => (
                <li key={w.regel} className={`admin-liste__eintrag admin-liste__eintrag--${w.stufe}`}>
                  <span className="admin-marke-klein">{w.regel}</span>
                  <span>{w.text}</span>
                </li>
              ))}
            </ul>
          )}

          <h2 className="admin-abschnitt">Quellen (letzte {daten.quellen[0]?.verlauf.length ?? 0} Läufe, neueste links)</h2>
          <div className="admin-tabelle-rahmen">
            <table className="admin-tabelle">
              <thead>
                <tr>
                  <th>Quelle</th>
                  <th>Verlauf</th>
                  <th>Letzter Erfolg</th>
                  <th>Hinweis</th>
                </tr>
              </thead>
              <tbody>
                {daten.quellen.map((q) => (
                  <tr key={q.quelle} className={q.warnungen.some((w) => w.stufe === "rot") ? "admin-zeile--rot" : q.warnungen.length ? "admin-zeile--gelb" : undefined}>
                    <td><strong>{q.quelle}</strong></td>
                    <td>
                      <span className="admin-verlauf">
                        {q.verlauf.map((v, i) => (
                          <span
                            key={i}
                            className={`admin-verlauf__punkt admin-verlauf__punkt--${v?.status ?? "fehlt"}`}
                            title={v ? `${STATUS_QUELLE[v.status]}: ${v.anzahl}` : "nicht dabei"}
                          >
                            {v && v.status === "ok" ? v.anzahl : ""}
                          </span>
                        ))}
                      </span>
                    </td>
                    <td>{zeit(q.letzterErfolg)}</td>
                    <td>
                      {q.warnungen.map((w) => (
                        <div key={w.regel}>
                          <span className="admin-marke-klein">{w.regel}</span> {w.text}
                        </div>
                      ))}
                      {!q.warnungen.length && q.letzteMeldung && <small>{q.letzteMeldung}</small>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 className="admin-abschnitt">Läufe</h2>
          <div className="admin-tabelle-rahmen">
            <table className="admin-tabelle">
              <thead>
                <tr>
                  <th>Start</th>
                  <th>Status</th>
                  <th>Dauer</th>
                  <th>Gesammelt</th>
                  <th>Neu</th>
                  <th>Duplikate</th>
                  <th>Auslöser</th>
                  <th>Log</th>
                </tr>
              </thead>
              <tbody>
                {daten.laeufe.map((l) => (
                  <tr key={l.id} className={l.status === "fehler" ? "admin-zeile--rot" : undefined}>
                    <td>{zeit(l.gestartet_am)}</td>
                    <td title={l.fehlermeldung ?? undefined}>{STATUS_LAUF[l.status]}</td>
                    <td>{dauer(l.gestartet_am, l.beendet_am)}</td>
                    <td>{l.events_gesammelt ?? "–"}</td>
                    <td>{l.neu_gespeichert ?? "–"}</td>
                    <td>{l.duplikate ?? "–"}</td>
                    <td>{l.ausloeser ?? "–"}</td>
                    <td>
                      {l.github_run_url ? (
                        <a href={l.github_run_url} target="_blank" rel="noreferrer noopener">
                          GitHub
                        </a>
                      ) : (
                        "–"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
