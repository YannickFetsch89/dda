"use client";
// Ein Tag der Wochenend-Box auf der Startseite. Vergangene Tage (Fr/Sa, Stand Sa oder So) sind mobil eingeklappt
// (Auftraggeber 16.11.2026): Der Kopf ist dann ein Knopf mit Pfeil, der die Tipps des Vortags aufklappt.
// Am Desktop (ab 1200 px, drei Spalten) ist jeder Tag offen; das regelt das CSS, der Zustand gilt nur mobil.
import { useId, useState, type ReactNode } from "react";

export function WochenendTag({ name, datum, vergangen, children }: { name: string; datum: string; vergangen: boolean; children: ReactNode }) {
  const [offen, setOffen] = useState(false);
  const inhaltId = useId();
  const kopf = (
    <>
      {name} <small>{datum}</small>
      {vergangen && <small className="band__vorbei">vorbei</small>}
    </>
  );
  if (!vergangen) {
    return (
      <div className="band__spalte">
        <span className="band__tag d">{kopf}</span>
        {children}
      </div>
    );
  }
  return (
    <div className={`band__spalte band__spalte--vergangen ${offen ? "is-offen" : ""}`}>
      <button type="button" className="band__tag band__klapper d" aria-expanded={offen} aria-controls={inhaltId} onClick={() => setOffen(!offen)}>
        <span>{kopf}</span>
        <span className="icon band__pfeil" aria-hidden data-icon="expand_more" />
      </button>
      <div id={inhaltId} className="band__inhalt">
        {children}
      </div>
    </div>
  );
}
