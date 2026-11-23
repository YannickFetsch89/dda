"use client";
// Vorschläge: Dubletten-Paare und Events außerhalb des Gebiets. Erst „Annehmen“ ändert Daten (DB-Funktionen).
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

interface Vorschlag {
  id: string;
  art: "dublette" | "gebiet";
  ziel_id: string | null;
  vorschlag: Record<string, unknown>;
  begruendung: string | null;
  status: string;
  erstellt_am: string;
}

const KOPF = { "Content-Type": "application/json" };
const ARTEN = [
  { wert: "", text: "alle" },
  { wert: "dublette", text: "Dubletten" },
  { wert: "gebiet", text: "außerhalb des Gebiets" },
];

function s(wert: unknown): string {
  return typeof wert === "string" ? wert : "";
}

export function VorschlagListe() {
  const [art, setArt] = useState("");
  const [liste, setListe] = useState<Vorschlag[] | null>(null);
  const [gesamt, setGesamt] = useState(0);
  const [fehler, setFehler] = useState<string | null>(null);
  const [arbeitet, setArbeitet] = useState<string | null>(null);

  const laden = useCallback(async () => {
    const r = await fetch(`/api/admin/vorschlaege${art ? `?art=${art}` : ""}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const d = (await r.json().catch(() => ({}))) as { vorschlaege?: Vorschlag[]; gesamt?: number; fehler?: string };
    if (!r.ok) return setFehler(d.fehler ?? "Vorschläge nicht ladbar.");
    setListe(d.vorschlaege ?? []);
    setGesamt(d.gesamt ?? 0);
  }, [art]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden bei Wechsel der Art
    laden();
  }, [laden]);

  async function entscheiden(v: Vorschlag, aktion: "annehmen" | "ablehnen") {
    setArbeitet(v.id);
    setFehler(null);
    const r = await fetch(`/api/admin/vorschlaege/${v.id}`, { method: "POST", headers: KOPF, body: JSON.stringify({ aktion }) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string };
    setArbeitet(null);
    if (!r.ok) return setFehler(d.fehler ?? "Hat nicht geklappt.");
    setListe((alt) => alt?.filter((x) => x.id !== v.id) ?? null);
    setGesamt((g) => Math.max(0, g - 1));
  }

  return (
    <>
      <h1>Vorschläge</h1>
      <p className="admin-unterzeile">
        Die Pipeline schlägt Dubletten und Events außerhalb von Düsseldorf, Neuss und Ratingen vor. Erst „Annehmen“ ändert etwas. Abgelehnte kommen nicht wieder.
      </p>
      <div className="admin-chips" role="group" aria-label="Art">
        {ARTEN.map((a) => (
          <button key={a.wert} type="button" className="admin-chip" aria-pressed={art === a.wert} onClick={() => setArt(a.wert)}>
            {a.text}
          </button>
        ))}
      </div>
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}
      {liste && <p className="admin-unterzeile">{gesamt} offen{gesamt > liste.length ? `, die neuesten ${liste.length} angezeigt` : ""}</p>}
      <ul className="admin-liste">
        {liste?.length === 0 && <li className="admin-liste__eintrag">Keine offenen Vorschläge.</li>}
        {liste?.map((v) => (
          <li key={v.id} className="admin-liste__eintrag admin-vorschlag">
            <span className="admin-marke-klein">{v.art === "dublette" ? "Dublette" : "Gebiet"}</span>
            {v.art === "dublette" ? (
              <div>
                <strong>{s(v.vorschlag.datum)}</strong> · {s(v.vorschlag.ort)}
                <br />
                Behalten: <Link href={`/admin/events/${s(v.vorschlag.behalten)}`}>{s(v.vorschlag.behalten_titel)}</Link>{" "}
                <small>({s(v.vorschlag.behalten_quelle)}, {s(v.vorschlag.behalten_uhrzeit) || "–"})</small>
                <br />
                Ausblenden: <Link href={`/admin/events/${s(v.vorschlag.dublette)}`}>{s(v.vorschlag.dublette_titel)}</Link>{" "}
                <small>({s(v.vorschlag.dublette_quelle)}, {s(v.vorschlag.dublette_uhrzeit) || "–"})</small>
              </div>
            ) : (
              <div>
                <Link href={`/admin/events/${s(v.vorschlag.event)}`}>{s(v.vorschlag.titel)}</Link> · {s(v.vorschlag.datum)}
                <br />
                <small>
                  {s(v.vorschlag.ort)} · {s(v.vorschlag.adresse) || "keine Adresse"} · {s(v.vorschlag.quelle)} · Grund: {s(v.vorschlag.grund)}
                </small>
              </div>
            )}
            <span className="admin-aktionen">
              <button type="button" className="admin-knopf" disabled={arbeitet === v.id} onClick={() => entscheiden(v, "annehmen")}>
                {v.art === "dublette" ? "Zusammenlegen" : "Entfernen"}
              </button>
              <button type="button" className="admin-knopf admin-knopf--leise" disabled={arbeitet === v.id} onClick={() => entscheiden(v, "ablehnen")}>
                Ablehnen
              </button>
            </span>
          </li>
        ))}
      </ul>
    </>
  );
}
