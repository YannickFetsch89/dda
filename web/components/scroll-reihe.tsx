"use client";
// Horizontal scrollende Reihe (Filter-Chips, Typ-Tabs): Ist Inhalt abgeschnitten, zeigen Pfeile links/rechts
// samt weicher Ausblendung, dass es weitergeht; ein Klick blättert um gut eine halbe Breite.
// Auf Touch-Geräten kann zusätzlich gewischt werden; Styles: .gd-scroll in globals.css.
// Ein aktiver Chip (z.B. ausgewählter Stadtteil) wird beim Laden in Sicht gerückt.
import { useEffect, useRef, useState, type ReactNode } from "react";

export function ScrollReihe({ className, label, children }: { className: string; label: string; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [links, setLinks] = useState(false);
  const [rechts, setRechts] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const pruefen = () => {
      setLinks(el.scrollLeft > 4);
      setRechts(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
    };
    // Aktiven Chip sichtbar machen, ohne die Seite vertikal zu bewegen
    const aktiv = el.querySelector<HTMLElement>(".gd-chip--an, [aria-current]");
    if (aktiv) {
      const a = aktiv.getBoundingClientRect();
      const r = el.getBoundingClientRect();
      if (a.right > r.right || a.left < r.left) el.scrollLeft += a.left - r.left - 48;
    }
    el.addEventListener("scroll", pruefen, { passive: true });
    // Größenänderungen (Fenster, nachgeladene Schrift) – plus einmal direkt nach dem Einbinden,
    // falls der Browser den ersten ResizeObserver-Aufruf verzögert (z.B. Hintergrund-Tab)
    const beobachter = new ResizeObserver(pruefen);
    beobachter.observe(el);
    const start = window.setTimeout(pruefen, 0);
    return () => {
      window.clearTimeout(start);
      el.removeEventListener("scroll", pruefen);
      beobachter.disconnect();
    };
  }, []);

  const blaettern = (richtung: 1 | -1) => {
    const el = ref.current;
    if (el) el.scrollBy({ left: richtung * Math.max(160, el.clientWidth * 0.6), behavior: "smooth" });
  };

  return (
    <div className={`gd-scroll${links ? " gd-scroll--links" : ""}${rechts ? " gd-scroll--rechts" : ""}`}>
      <button type="button" className="gd-scroll__pfeil gd-scroll__pfeil--links" onClick={() => blaettern(-1)}
        aria-label={`${label}: nach links blättern`} tabIndex={-1} hidden={!links}>
        <span className="icon" aria-hidden>chevron_left</span>
      </button>
      <div ref={ref} className={className}>
        {children}
      </div>
      <button type="button" className="gd-scroll__pfeil gd-scroll__pfeil--rechts" onClick={() => blaettern(1)}
        aria-label={`${label}: nach rechts blättern`} tabIndex={-1} hidden={!rechts}>
        <span className="icon" aria-hidden>chevron_right</span>
      </button>
    </div>
  );
}
