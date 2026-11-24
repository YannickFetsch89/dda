"use client";
// Quellen an/aus (Plan Admin-Dashboard 4.10, Stufe 5b): Schalter je Quelle des letzten Laufs. main.py überspringt
// abgeschaltete Quellen ab dem nächsten Lauf; ihre Events bleiben.
import { useCallback, useEffect, useState } from "react";

interface Quelle {
  quelle: string;
  tier: number | null;
  status: string | null;
  anzahl: number | null;
  meldung: string | null;
  aktiv: boolean;
  grund: string | null;
}

export function QuellenSchalter() {
  const [liste, setListe] = useState<Quelle[] | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState<string | null>(null);

  const laden = useCallback(async () => {
    const r = await fetch("/api/admin/quellen", { cache: "no-store" });
    const d = (await r.json().catch(() => ({}))) as { quellen?: Quelle[]; fehler?: string };
    if (!r.ok) return setFehler(d.fehler ?? "Quellen nicht ladbar.");
    setListe(d.quellen ?? []);
    setFehler(null);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden
    laden();
  }, [laden]);

  async function schalten(q: Quelle) {
    let grund = "";
    if (q.aktiv) {
      grund = window.prompt(`„${q.quelle}“ abschalten? Kurzer Grund (z. B. Seite umgebaut, liefert Unsinn):`) ?? "";
      if (!grund.trim()) return;
    } else if (!window.confirm(`„${q.quelle}“ wieder einschalten? Sie läuft ab dem nächsten Scraper-Lauf.`)) return;
    setLaeuft(q.quelle);
    const r = await fetch("/api/admin/quellen", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ quelle: q.quelle, aktiv: !q.aktiv, grund }) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string };
    setLaeuft(null);
    if (!r.ok) return setFehler(d.fehler ?? "Hat nicht geklappt.");
    laden();
  }

  return (
    <section className="admin-karte">
      <h2>Quellen an/aus</h2>
      <p className="admin-unterzeile">Abgeschaltete Quellen überspringt der nächste Lauf (Report: „uebersprungen“, keine Warnung). Ihre Events bleiben.</p>
      {fehler && <p className="admin-fehler">{fehler}</p>}
      {liste && (
        <ul className="admin-liste">
          {liste.map((q) => (
            <li key={q.quelle} className="admin-liste__eintrag">
              <strong>{q.quelle}</strong>
              <span>
                {q.tier ? `Tier ${q.tier} · ` : ""}
                {q.aktiv ? "an" : `aus${q.grund ? ` (${q.grund})` : ""}`}
                {q.status ? ` · letzter Lauf: ${q.status}${q.anzahl !== null ? `, ${q.anzahl} Events` : ""}` : ""}
              </span>
              <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft === q.quelle} onClick={() => schalten(q)}>
                {q.aktiv ? "Abschalten" : "Einschalten"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
