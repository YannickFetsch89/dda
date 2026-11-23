"use client";
// Protokoll aller schreibenden Admin-Aktionen (Plan Admin-Dashboard 4.10, Stufe 5a) mit Filter und „Rückgängig“ für
// einfache Feldänderungen an Events und Orten.
import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { RUECKGAENGIG_AKTIONEN } from "@/lib/admin/rueckgaengig";

interface Eintrag {
  id: string;
  zeitpunkt: string;
  aktion: string;
  tabelle: string | null;
  ziel_id: string | null;
  vorher: unknown;
  nachher: unknown;
}

function zeit(iso: string): string {
  return new Date(iso).toLocaleString("de-DE", { timeZone: "Europe/Berlin", dateStyle: "short", timeStyle: "short" });
}

function kurz(w: unknown): string {
  if (w === null || w === undefined) return "–";
  const s = JSON.stringify(w);
  return s.length > 220 ? `${s.slice(0, 220)} …` : s;
}

function zielLink(e: Eintrag): string | null {
  if (!e.ziel_id || !/^[0-9a-f-]{36}$/i.test(e.ziel_id)) return null;
  if (e.tabelle === "events") return `/admin/events/${e.ziel_id}`;
  if (e.tabelle === "orte") return `/admin/orte/${e.ziel_id}`;
  if (e.tabelle === "magazin_beitraege") return `/admin/magazin/${e.ziel_id}`;
  return null;
}

export function ProtokollListe() {
  const [filter, setFilter] = useState({ aktion: "", tabelle: "" });
  const [seite, setSeite] = useState(0);
  const [d, setD] = useState<{ gesamt: number; proSeite: number; eintraege: Eintrag[] } | null>(null);
  const [meldung, setMeldung] = useState<{ art: "ok" | "fehler"; text: string } | null>(null);

  const laden = useCallback(async () => {
    const p = new URLSearchParams();
    if (filter.aktion) p.set("aktion", filter.aktion);
    if (filter.tabelle) p.set("tabelle", filter.tabelle);
    if (seite) p.set("seite", String(seite));
    const r = await fetch(`/api/admin/protokoll?${p.toString()}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const x = (await r.json().catch(() => ({}))) as { gesamt: number; proSeite: number; eintraege: Eintrag[]; fehler?: string };
    if (!r.ok) return setMeldung({ art: "fehler", text: x.fehler ?? "Nicht ladbar." });
    setD(x);
  }, [filter, seite]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden bei Filter- und Seitenwechsel
    laden();
  }, [laden]);

  async function rueckgaengig(e: Eintrag) {
    if (!window.confirm("Diese Änderung zurücknehmen? Die alten Werte werden wieder eingetragen (als neue Redaktionsänderung).")) return;
    const r = await fetch("/api/admin/protokoll", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ aktion: "rueckgaengig", id: e.id }) });
    const x = (await r.json().catch(() => ({}))) as { fehler?: string; geaendert?: string[] };
    setMeldung(r.ok ? { art: "ok", text: x.geaendert?.length ? `Zurückgenommen: ${x.geaendert.join(", ")}.` : "Nichts mehr zu ändern." } : { art: "fehler", text: x.fehler ?? "Hat nicht geklappt." });
    if (r.ok) laden();
  }

  function suchen(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const f = new FormData(ev.currentTarget);
    setSeite(0);
    setFilter({ aktion: String(f.get("aktion") ?? "").trim(), tabelle: String(f.get("tabelle") ?? "").trim() });
  }

  const seiten = d ? Math.ceil(d.gesamt / d.proSeite) : 0;

  return (
    <>
      <h1>Protokoll</h1>
      <p className="admin-unterzeile">Jede schreibende Aktion im Admin-Bereich. Einträge lassen sich nicht ändern oder löschen.</p>
      <form className="admin-karte admin-filterleiste" onSubmit={suchen}>
        <label className="admin-feld">
          Aktion beginnt mit
          <input name="aktion" defaultValue={filter.aktion} placeholder="z. B. event_, ort_, vorschlag_" />
        </label>
        <label className="admin-feld">
          Tabelle
          <select name="tabelle" defaultValue={filter.tabelle}>
            <option value="">alle</option>
            {["events", "orte", "magazin_beitraege", "admin_vorschlaege", "newsletter_anmeldungen", "event_sensibel"].map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <button className="admin-knopf" type="submit">
          Filtern
        </button>
      </form>
      {meldung && <p className={meldung.art === "ok" ? "admin-karte" : "admin-fehler"} role="status">{meldung.text}</p>}
      {d && (
        <div className="admin-tabelle-rahmen">
          <table className="admin-tabelle">
            <thead>
              <tr>
                <th>Zeit</th>
                <th>Aktion</th>
                <th>Ziel</th>
                <th>vorher → nachher</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {d.eintraege.length === 0 && (
                <tr>
                  <td colSpan={5}>Keine Einträge.</td>
                </tr>
              )}
              {d.eintraege.map((e) => {
                const link = zielLink(e);
                return (
                  <tr key={e.id}>
                    <td>{zeit(e.zeitpunkt)}</td>
                    <td>
                      {e.aktion}
                      <br />
                      <small>{e.tabelle ?? ""}</small>
                    </td>
                    <td>{link ? <Link href={link}>öffnen</Link> : <small>{e.ziel_id ?? "–"}</small>}</td>
                    <td>
                      <small>
                        {kurz(e.vorher)}
                        <br />→ {kurz(e.nachher)}
                      </small>
                    </td>
                    <td>
                      {(RUECKGAENGIG_AKTIONEN as readonly string[]).includes(e.aktion) && (
                        <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => rueckgaengig(e)}>
                          Rückgängig
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {seiten > 1 && (
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
