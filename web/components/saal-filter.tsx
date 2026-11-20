"use client";
// Saal-Filter für „Nächste Events“ auf Guide-Seiten mit Sälen (Plan docs/plan-locations-2026-11-18.md, 3.6):
// dieselben Gruppen wie auf der Ortsseite („Alle“, je Saal, „Haus allgemein“). Die Listen rendert der Server
// vorab; hier wird nur umgeschaltet – ohne Suchparameter, damit die Guide-Seite statisch bleibt.
import Link from "next/link";
import { useState, type ReactNode } from "react";

export interface SaalGruppe {
  id: string;
  label: string;
  /** Eigene Ortsseite des Saals (fehlt bei „Alle“ und „Haus allgemein“) */
  href: string | null;
  anzahl: number;
  inhalt: ReactNode;
}

export function SaalFilter({ gruppen }: { gruppen: SaalGruppe[] }) {
  const [wahl, setWahl] = useState(gruppen[0]?.id ?? "");
  const aktiv = gruppen.find((g) => g.id === wahl) ?? gruppen[0];
  if (!aktiv) return null;
  return (
    <>
      <div className="os-saele" role="group" aria-label="Nach Saal filtern">
        {gruppen.map((g) => (
          <button key={g.id} type="button" className={`gd-chip${g.id === aktiv.id ? " gd-chip--an" : ""}`}
            aria-pressed={g.id === aktiv.id} onClick={() => setWahl(g.id)}>
            {g.label}
          </button>
        ))}
      </div>
      {aktiv.anzahl > 0 ? aktiv.inhalt : <p className="muted">Gerade keine kommenden Termine.</p>}
      {aktiv.href && (
        <p className="os-saal-link">
          <Link href={aktiv.href} className="link">Alle Termine und Infos: {aktiv.label} →</Link>
        </p>
      )}
    </>
  );
}
