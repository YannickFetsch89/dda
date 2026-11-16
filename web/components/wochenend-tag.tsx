"use client";
// Ein Tag der Wochenend-Box auf der Startseite. Vergangene Tage (Fr/Sa, Stand Sa oder So) sind mobil eingeklappt
// (Auftraggeber 16.11.2026): Der Kopf ist dann ein Knopf mit Pfeil, der die Tipps des Vortags aufklappt.
// Am Desktop (ab 1200 px, drei Spalten) ist jeder Tag offen und der Kopf kein Knopf (Cursor-Prüfung 16.11.2026:
// sonst bliebe ein per Tastatur erreichbarer Knopf mit aria-expanded=false über einer sichtbaren Liste).
import { useId, useState, useSyncExternalStore, type ReactNode } from "react";

const DESKTOP = "(min-width: 1200px)";
const desktopAbonnieren = (melden: () => void) => {
  const mq = window.matchMedia(DESKTOP);
  mq.addEventListener("change", melden);
  return () => mq.removeEventListener("change", melden);
};
const istDesktop = () => window.matchMedia(DESKTOP).matches;

export function WochenendTag({ name, datum, vergangen, children }: { name: string; datum: string; vergangen: boolean; children: ReactNode }) {
  const [offen, setOffen] = useState(false);
  // Server: mobil (eingeklappt per CSS bleibt korrekt); im Browser die echte Breite
  const desktop = useSyncExternalStore(desktopAbonnieren, istDesktop, () => false);
  const inhaltId = useId();
  const kopf = (
    <>
      {name} <small>{datum}</small>
      {vergangen && <small className="band__vorbei">vorbei</small>}
    </>
  );
  if (!vergangen || desktop) {
    return (
      <div className={`band__spalte ${vergangen ? "band__spalte--vergangen is-offen" : ""}`}>
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
