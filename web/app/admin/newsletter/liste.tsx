"use client";
// Newsletter-Anmeldungen: Zahlen, Liste (bestätigt / offen), Export der Bestätigten, Löschen auf Anfrage.
// Abgemeldete gibt es nicht: Abmelden löscht die Adresse sofort (Datenschutzerklärung Abschnitt 11).
import { useCallback, useEffect, useState, type FormEvent } from "react";

interface Anmeldung {
  id: string;
  email: string;
  quelle: string | null;
  erstellt_am: string;
  bestaetigt_am: string | null;
  bestaetigung_gesendet_am: string | null;
  bestaetigung_zugestellt_am: string | null;
  mails_gesendet: number | null;
}

interface Zahlen {
  bestaetigt: number;
  wartet_auf_bestaetigung: number;
  mail_steht_aus: number;
  neu_7_tage: number;
}

interface Antwort {
  seite: number;
  proSeite: number;
  gesamt: number;
  anmeldungen: Anmeldung[];
  zahlen: Zahlen | null;
}

const STATUS = [
  { wert: "", text: "alle" },
  { wert: "bestaetigt", text: "bestätigt" },
  { wert: "offen", text: "nicht bestätigt" },
];

function zeit(iso: string | null): string {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("de-DE", { timeZone: "Europe/Berlin", dateStyle: "short", timeStyle: "short" });
}

export function NewsletterListe() {
  const [status, setStatus] = useState("");
  const [suche, setSuche] = useState("");
  const [seite, setSeite] = useState(0);
  const [d, setD] = useState<Antwort | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

  const laden = useCallback(async () => {
    // POST: Eine gesuchte Adresse steht so weder in der Adresszeile noch im Access-Log (Cursor-Prüfung 4, Befund 2)
    const r = await fetch("/api/admin/newsletter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aktion: "liste", status, q: suche, seite }),
      cache: "no-store",
    });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const x = (await r.json().catch(() => ({}))) as Antwort & { fehler?: string };
    if (!r.ok) return setFehler(x.fehler ?? "Liste nicht ladbar.");
    setD(x);
    setFehler(null);
  }, [status, suche, seite]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden bei Wechsel von Filter und Seite
    laden();
  }, [laden]);

  async function loeschen(a: Anmeldung) {
    if (!window.confirm(`${a.email} endgültig löschen? Das lässt sich nicht rückgängig machen.`)) return;
    const r = await fetch("/api/admin/newsletter", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ aktion: "loeschen", id: a.id }) });
    const x = (await r.json().catch(() => ({}))) as { fehler?: string };
    if (!r.ok) return setFehler(x.fehler ?? "Löschen hat nicht geklappt.");
    laden();
  }

  function suchen(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSeite(0);
    setSuche(String(new FormData(e.currentTarget).get("q") ?? "").trim());
  }

  const z = d?.zahlen;
  const seiten = d ? Math.ceil(d.gesamt / d.proSeite) : 0;

  return (
    <>
      <h1>Newsletter</h1>
      <p className="admin-unterzeile">
        Double-Opt-in. Unbestätigte Adressen werden 30 Tage nach der Mail gelöscht, Abmelden löscht sofort. Der Versand des Newsletters selbst ist
        ein eigener Plan.
      </p>
      {z && (
        <div className="admin-kacheln">
          <div className="admin-karte">
            <strong>{z.bestaetigt}</strong> bestätigt
          </div>
          <div className="admin-karte">
            <strong>{z.wartet_auf_bestaetigung}</strong> warten auf Bestätigung
          </div>
          <div className="admin-karte">
            <strong>{z.mail_steht_aus}</strong> Mail steht aus
          </div>
          <div className="admin-karte">
            <strong>{z.neu_7_tage}</strong> neu in 7 Tagen
          </div>
        </div>
      )}
      <form className="admin-karte admin-filterleiste" onSubmit={suchen}>
        <label className="admin-feld">
          Adresse suchen
          <input name="q" defaultValue={suche} />
        </label>
        <button className="admin-knopf" type="submit">
          Suchen
        </button>
        <a className="admin-knopf admin-knopf--leise" href="/api/admin/newsletter?export=1">
          Bestätigte als CSV
        </a>
      </form>
      <div className="admin-chips" role="group" aria-label="Status">
        {STATUS.map((s) => (
          <button
            key={s.wert}
            type="button"
            className="admin-chip"
            aria-pressed={status === s.wert}
            onClick={() => {
              setSeite(0);
              setStatus(s.wert);
            }}
          >
            {s.text}
          </button>
        ))}
      </div>
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}
      {d && (
        <div className="admin-tabelle-rahmen">
          <table className="admin-tabelle">
            <thead>
              <tr>
                <th>Adresse</th>
                <th>Angemeldet</th>
                <th>Bestätigungsmail</th>
                <th>Bestätigt</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {d.anmeldungen.length === 0 && (
                <tr>
                  <td colSpan={5}>Keine Anmeldungen.</td>
                </tr>
              )}
              {d.anmeldungen.map((a) => (
                <tr key={a.id} className={a.bestaetigt_am ? undefined : "admin-zeile--grau"}>
                  <td>{a.email}</td>
                  <td>{zeit(a.erstellt_am)}</td>
                  <td>
                    {zeit(a.bestaetigung_zugestellt_am)}
                    {(a.mails_gesendet ?? 0) > 1 && <small> ({a.mails_gesendet}×)</small>}
                  </td>
                  <td>{zeit(a.bestaetigt_am)}</td>
                  <td>
                    <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => loeschen(a)}>
                      Löschen
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {seiten > 1 && d && (
        <nav className="admin-seiten" aria-label="Seiten">
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={seite === 0} onClick={() => setSeite(seite - 1)}>
            zurück
          </button>
          <span>
            Seite {seite + 1} von {seiten}
          </span>
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={seite + 1 >= seiten} onClick={() => setSeite(seite + 1)}>
            weiter
          </button>
        </nav>
      )}
    </>
  );
}
