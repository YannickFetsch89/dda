"use client";
// Vorschläge: Dubletten-Paare, Events außerhalb des Gebiets und (Stufe 3c) Ortsnamen, Ortszuordnung, Adressen.
// Erst „Annehmen“ ändert Daten (DB-Funktionen). Die Orte-Arten lassen sich auch gesammelt entscheiden.
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { SAMMEL_ARTEN, VORSCHLAG_ARTEN } from "@/lib/admin/vorschlaege";

interface Vorschlag {
  id: string;
  art: string;
  ziel_id: string | null;
  vorschlag: Record<string, unknown>;
  begruendung: string | null;
  status: string;
  erstellt_am: string;
}

const KOPF = { "Content-Type": "application/json" };
const ARTEN = [{ wert: "", text: "alle" }, ...VORSCHLAG_ARTEN.map((a) => ({ wert: a.wert as string, text: a.text }))];
const MARKE = new Map<string, string>(VORSCHLAG_ARTEN.map((a) => [a.wert, a.marke]));
const ANNEHMEN_TEXT: Record<string, string> = {
  dublette: "Zusammenlegen",
  gebiet: "Entfernen",
  ortsname: "Umbenennen",
  ort_id: "Zuordnen",
  adresse: "Übernehmen",
};

function s(wert: unknown): string {
  return typeof wert === "string" ? wert : "";
}

function Inhalt({ v }: { v: Vorschlag }) {
  const x = v.vorschlag;
  if (v.art === "dublette") {
    return (
      <div>
        <strong>{s(x.datum)}</strong> · {s(x.ort)}
        <br />
        Behalten: <Link href={`/admin/events/${s(x.behalten)}`}>{s(x.behalten_titel)}</Link>{" "}
        <small>({s(x.behalten_quelle)}, {s(x.behalten_uhrzeit) || "–"})</small>
        <br />
        Ausblenden: <Link href={`/admin/events/${s(x.dublette)}`}>{s(x.dublette_titel)}</Link>{" "}
        <small>({s(x.dublette_quelle)}, {s(x.dublette_uhrzeit) || "–"})</small>
      </div>
    );
  }
  if (v.art === "gebiet") {
    return (
      <div>
        <Link href={`/admin/events/${s(x.event)}`}>{s(x.titel)}</Link> · {s(x.datum)}
        <br />
        <small>
          {s(x.ort)} · {s(x.adresse) || "keine Adresse"} · {s(x.quelle)} · Grund: {s(x.grund)}
        </small>
      </div>
    );
  }
  if (v.art === "ortsname") {
    const anzahl = Array.isArray(x.events) ? x.events.length : 0;
    return (
      <div>
        „{s(x.alt)}“ → <strong>„{s(x.neu)}“</strong>
        <br />
        <small>{anzahl} Events · Liste in pipeline/ortsnamen.py · von der Redaktion geänderte Orte bleiben</small>
      </div>
    );
  }
  if (v.art === "ort_id") {
    return (
      <div>
        <Link href={`/admin/events/${s(x.event)}`}>{s(x.titel)}</Link> · {s(x.datum)}
        <br />
        <small>
          „{s(x.ort)}“ → <Link href={`/admin/orte/${s(x.ort_id)}`}>{s(x.ort_name)}</Link> ({s(x.ort_typ)}){x.bisher ? " · ersetzt eine andere Zuordnung" : ""}
        </small>
      </div>
    );
  }
  return (
    <div>
      <Link href={`/admin/events/${s(x.event)}`}>{s(x.titel)}</Link> · {s(x.datum)}
      <br />
      <small>
        „{s(x.ort)}“ → {s(x.adresse)}
        {s(x.stadtteil) ? ` · ${s(x.stadtteil)}` : ""}
      </small>
    </div>
  );
}

export function VorschlagListe() {
  const [art, setArt] = useState("");
  const [liste, setListe] = useState<Vorschlag[] | null>(null);
  const [gesamt, setGesamt] = useState(0);
  const [fehler, setFehler] = useState<string | null>(null);
  const [meldung, setMeldung] = useState<string | null>(null);
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
    setMeldung(null);
    const r = await fetch(`/api/admin/vorschlaege/${v.id}`, { method: "POST", headers: KOPF, body: JSON.stringify({ aktion }) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string; ergebnis?: { geaendert?: number } };
    setArbeitet(null);
    if (!r.ok) return setFehler(d.fehler ?? "Hat nicht geklappt.");
    if (aktion === "annehmen" && d.ergebnis?.geaendert === 0) setMeldung("Angenommen – es war nichts mehr zu ändern (Feld schon gesetzt oder von der Redaktion geschützt).");
    setListe((alt) => alt?.filter((x) => x.id !== v.id) ?? null);
    setGesamt((g) => Math.max(0, g - 1));
  }

  async function alleEntscheiden(aktion: "annehmen" | "ablehnen") {
    if (!liste?.length) return;
    const text = aktion === "annehmen" ? `Alle ${liste.length} angezeigten Vorschläge annehmen?` : `Alle ${liste.length} angezeigten Vorschläge ablehnen? Sie kommen nicht wieder.`;
    if (!window.confirm(text)) return;
    setArbeitet("alle");
    setFehler(null);
    setMeldung(null);
    const r = await fetch("/api/admin/vorschlaege/sammel", { method: "POST", headers: KOPF, body: JSON.stringify({ aktion, ids: liste.map((v) => v.id) }) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string | { fehler: string }[]; erledigt?: number };
    setArbeitet(null);
    if (!r.ok) return setFehler(typeof d.fehler === "string" ? d.fehler : "Hat nicht geklappt.");
    const fehlerListe = Array.isArray(d.fehler) ? d.fehler : [];
    setMeldung(`${d.erledigt ?? 0} erledigt${fehlerListe.length ? `, ${fehlerListe.length} mit Fehler: ${fehlerListe[0].fehler}` : ""}.`);
    laden();
  }

  const sammelbar = SAMMEL_ARTEN.includes(art) && !!liste?.length;

  return (
    <>
      <h1>Vorschläge</h1>
      <p className="admin-unterzeile">
        Die Pipeline schlägt Dubletten, Events außerhalb von Düsseldorf, Neuss und Ratingen, einheitliche Ortsnamen, Ortszuordnungen und Adressen vor.
        Erst „Annehmen“ ändert etwas; von der Redaktion geänderte Felder bleiben. Abgelehnte kommen nicht wieder.
      </p>
      <div className="admin-chips" role="group" aria-label="Art">
        {ARTEN.map((a) => (
          <button key={a.wert} type="button" className="admin-chip" aria-pressed={art === a.wert} onClick={() => setArt(a.wert)}>
            {a.text}
          </button>
        ))}
      </div>
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}
      {meldung && <p className="admin-karte" role="status">{meldung}</p>}
      {liste && <p className="admin-unterzeile">{gesamt} offen{gesamt > liste.length ? `, die ${liste.length} ersten angezeigt` : ""}</p>}
      {sammelbar && (
        <div className="admin-knopfreihe">
          <button type="button" className="admin-knopf" disabled={arbeitet !== null} onClick={() => alleEntscheiden("annehmen")}>
            Alle {liste!.length} angezeigten annehmen
          </button>
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={arbeitet !== null} onClick={() => alleEntscheiden("ablehnen")}>
            Alle angezeigten ablehnen
          </button>
        </div>
      )}
      <ul className="admin-liste">
        {liste?.length === 0 && <li className="admin-liste__eintrag">Keine offenen Vorschläge.</li>}
        {liste?.map((v) => (
          <li key={v.id} className="admin-liste__eintrag admin-vorschlag">
            <span className="admin-marke-klein">{MARKE.get(v.art) ?? v.art}</span>
            <Inhalt v={v} />
            <span className="admin-aktionen">
              <button type="button" className="admin-knopf" disabled={arbeitet !== null} onClick={() => entscheiden(v, "annehmen")}>
                {ANNEHMEN_TEXT[v.art] ?? "Annehmen"}
              </button>
              <button type="button" className="admin-knopf admin-knopf--leise" disabled={arbeitet !== null} onClick={() => entscheiden(v, "ablehnen")}>
                Ablehnen
              </button>
            </span>
          </li>
        ))}
      </ul>
    </>
  );
}
