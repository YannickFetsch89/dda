"use client";
// SEO-Aufräumen (Plan Admin-Dashboard 4.10, Stufe 5b; Umzug aus dashboard/seo_aufraeumen.py): Events, die seit mehr
// als 12 Monaten vorbei sind – auswählen und entscheiden (behalten, 301, 410) oder zurücknehmen.
import { useCallback, useEffect, useState } from "react";

interface Zeile {
  id: string;
  datum: string;
  titel: string;
  ort: string | null;
  kategorie: string;
  reihe: string | null;
  pfad: string;
  entscheidung: string | null;
  ziel: string | null;
}

interface Antwort {
  gesamt: number;
  entschieden: number;
  offen: number;
  mehr: boolean;
  zeilen: Zeile[];
  aktionen: Record<string, string>;
}

export function SeoListe() {
  const [nurOffen, setNurOffen] = useState(true);
  const [d, setD] = useState<Antwort | null>(null);
  const [auswahl, setAuswahl] = useState<Set<string>>(new Set());
  const [art, setArt] = useState("behalten");
  const [meldung, setMeldung] = useState<{ text: string; art: "ok" | "fehler" } | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  const laden = useCallback(async () => {
    const r = await fetch(`/api/admin/seo?offen=${nurOffen ? 1 : 0}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const x = (await r.json().catch(() => ({}))) as Antwort & { fehler?: string };
    if (!r.ok) return setMeldung({ text: x.fehler ?? "Nicht ladbar.", art: "fehler" });
    setD(x);
    setAuswahl(new Set());
  }, [nurOffen]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden bei Wechsel des Filters
    laden();
  }, [laden]);

  async function senden(body: Record<string, unknown>, okText: (x: { anzahl?: number; uebersprungen?: number }) => string) {
    setLaeuft(true);
    const r = await fetch("/api/admin/seo", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const x = (await r.json().catch(() => ({}))) as { fehler?: string; anzahl?: number; uebersprungen?: number };
    setLaeuft(false);
    setMeldung(r.ok ? { text: okText(x), art: "ok" } : { text: x.fehler ?? "Hat nicht geklappt.", art: "fehler" });
    if (r.ok) laden();
  }

  function umschalten(id: string) {
    const neu = new Set(auswahl);
    if (neu.has(id)) neu.delete(id);
    else neu.add(id);
    setAuswahl(neu);
  }

  return (
    <>
      <h1>SEO-Aufräumen</h1>
      <p className="admin-unterzeile">
        Events, die seit mehr als 12 Monaten vorbei sind. Entscheide anhand der Search-Console-Daten – nichts passiert automatisch. Weiterleitungen
        gehen nie auf die Startseite. 301 und 410 sind für Google dauerhafte Signale. Die Website übernimmt Entscheidungen innerhalb von 10 Minuten.
      </p>
      {d && (
        <div className="admin-kacheln">
          <div className="admin-karte"><strong>{d.gesamt}</strong> seit &gt; 12 Monaten vorbei</div>
          <div className="admin-karte"><strong>{d.entschieden}</strong> entschieden</div>
          <div className="admin-karte"><strong>{d.offen}</strong> offen</div>
        </div>
      )}
      <div className="admin-filterleiste admin-karte">
        <label className="admin-schalter">
          <input type="checkbox" checked={nurOffen} onChange={(e) => setNurOffen(e.target.checked)} /> nur noch nicht entschiedene
        </label>
        <a className="admin-knopf admin-knopf--leise" href={`/api/admin/seo?export=1&offen=${nurOffen ? 1 : 0}`}>
          CSV der angezeigten
        </a>
      </div>
      {meldung && <p className={meldung.art === "ok" ? "admin-karte" : "admin-fehler"} role="status">{meldung.text}</p>}
      {d?.mehr && <p className="admin-unterzeile">Gezeigt werden die ältesten {d.zeilen.length}; nach dem Entscheiden rücken die nächsten nach.</p>}
      {d && d.zeilen.length > 0 && (
        <>
          <div className="admin-filterleiste">
            <label className="admin-schalter">
              <input
                type="checkbox"
                checked={auswahl.size === d.zeilen.length}
                onChange={(e) => setAuswahl(e.target.checked ? new Set(d.zeilen.map((z) => z.id)) : new Set())}
              />{" "}
              alle {d.zeilen.length} auswählen
            </label>
            <label className="admin-feld">
              Entscheidung
              <select value={art} onChange={(e) => setArt(e.target.value)}>
                {Object.entries(d.aktionen).map(([k, t]) => (
                  <option key={k} value={k}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="admin-knopf"
              disabled={!auswahl.size || laeuft}
              onClick={() =>
                window.confirm(`Für ${auswahl.size} Event(s) „${d.aktionen[art]}“ speichern?`) &&
                senden({ aktion: "entscheiden", ids: [...auswahl], art }, (x) => `${x.anzahl ?? 0} gespeichert${x.uebersprungen ? `, ${x.uebersprungen} ohne passendes Ziel übersprungen` : ""}.`)
              }
            >
              Für {auswahl.size} speichern
            </button>
            <button
              type="button"
              className="admin-knopf admin-knopf--leise"
              disabled={!auswahl.size || laeuft}
              onClick={() => window.confirm(`Entscheidung für ${auswahl.size} Event(s) zurücknehmen?`) && senden({ aktion: "zuruecknehmen", ids: [...auswahl] }, (x) => `${x.anzahl ?? 0} zurückgenommen.`)}
            >
              Zurücknehmen
            </button>
          </div>
          <div className="admin-tabelle-rahmen">
            <table className="admin-tabelle">
              <thead>
                <tr>
                  <th />
                  <th>Datum</th>
                  <th>Titel</th>
                  <th>Ort</th>
                  <th>Kategorie</th>
                  <th>Reihe</th>
                  <th>Entscheidung</th>
                </tr>
              </thead>
              <tbody>
                {d.zeilen.map((z) => (
                  <tr key={z.id}>
                    <td>
                      <input type="checkbox" checked={auswahl.has(z.id)} onChange={() => umschalten(z.id)} aria-label={`${z.titel} auswählen`} />
                    </td>
                    <td>{z.datum}</td>
                    <td>
                      <a href={`https://diesdas.events${z.pfad}`} target="_blank" rel="noreferrer noopener">
                        {z.titel}
                      </a>
                    </td>
                    <td>{z.ort ?? "–"}</td>
                    <td>{z.kategorie}</td>
                    <td>{z.reihe ?? "–"}</td>
                    <td>
                      {z.entscheidung ?? "–"}
                      {z.ziel && <small> → {z.ziel}</small>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {d && !d.gesamt && <p className="admin-karte">Noch keine Events, die seit mehr als 12 Monaten vorbei sind.</p>}
    </>
  );
}
