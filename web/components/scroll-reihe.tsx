"use client";
// Horizontal scrollende Reihe (Filter-Chips, Typ-Tabs): Ist Inhalt abgeschnitten, zeigen Pfeile links/rechts
// samt weicher Ausblendung, dass es weitergeht; ein Klick blättert um gut eine halbe Breite.
// Auf Touch-Geräten kann zusätzlich gewischt werden; Styles: .gd-scroll in globals.css.
// Ein aktiver Chip (z.B. ausgewählter Stadtteil) wird beim Laden in Sicht gerückt.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

export function ScrollReihe({
  className,
  label,
  aktivZeigen = true,
  children,
}: {
  className: string;
  label: string;
  /** Aktiven Chip in Sicht rücken – nur für Reihen mit Einfachauswahl (Typ, Stadtteil) sinnvoll */
  aktivZeigen?: boolean;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [links, setLinks] = useState(false);
  const [rechts, setRechts] = useState(false);

  const pruefen = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    setLinks(el.scrollLeft > 4);
    setRechts(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
  }, []);

  // Einmal: Scrollen und Größenänderungen (Fenster, nachgeladene Schrift) beobachten
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.addEventListener("scroll", pruefen, { passive: true });
    const beobachter = new ResizeObserver(pruefen);
    beobachter.observe(el);
    return () => {
      el.removeEventListener("scroll", pruefen);
      beobachter.disconnect();
    };
  }, [pruefen]);

  // Bei jedem neuen Inhalt (auch nach Filterwechsel per Client-Navigation, die Komponente bleibt
  // gemountet): aktiven Chip in Sicht rücken und Pfeile neu bestimmen – die Breite der Leiste ändert
  // sich dabei oft nicht, der ResizeObserver allein meldet sich dann nicht
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (aktivZeigen) {
      const aktiv = el.querySelector<HTMLElement>(".gd-chip--an, [aria-current]");
      if (aktiv) {
        const a = aktiv.getBoundingClientRect();
        const r = el.getBoundingClientRect();
        if (a.right > r.right || a.left < r.left) el.scrollLeft += a.left - r.left - 48;
      }
    }
    const t = window.setTimeout(pruefen, 0);
    return () => window.clearTimeout(t);
  }, [children, aktivZeigen, pruefen]);

  const blaettern = (richtung: 1 | -1) => {
    const el = ref.current;
    if (el) el.scrollBy({ left: richtung * Math.max(160, el.clientWidth * 0.6), behavior: "smooth" });
  };

  return (
    <div className={`gd-scroll${links ? " gd-scroll--links" : ""}${rechts ? " gd-scroll--rechts" : ""}`}>
      <button type="button" className="gd-scroll__pfeil gd-scroll__pfeil--links" onClick={() => blaettern(-1)}
        aria-label={`${label}: nach links blättern`} tabIndex={-1} hidden={!links}>
        <span className="icon" aria-hidden data-icon="chevron_left" />
      </button>
      <div ref={ref} className={className}>
        {children}
      </div>
      <button type="button" className="gd-scroll__pfeil gd-scroll__pfeil--rechts" onClick={() => blaettern(1)}
        aria-label={`${label}: nach rechts blättern`} tabIndex={-1} hidden={!rechts}>
        <span className="icon" aria-hidden data-icon="chevron_right" />
      </button>
    </div>
  );
}
