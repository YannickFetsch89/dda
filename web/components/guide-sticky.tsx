"use client";
// Kompakte Filterleiste (Design-Ansicht 15): erscheint oben fixiert, sobald die große Filterleiste
// aus dem Bild gescrollt ist. Zeigt Typ-Tabs, aktive Filter als Chips mit ×, "Filter"-Button
// (springt zurück zur vollständigen Leiste) und die Sortierung.
import Link from "next/link";
import { useEffect, useState } from "react";

export interface StickyLink {
  label: string;
  href: string;
  aktiv?: boolean;
  icon?: string;
}

export function GuideSticky({
  zielId,
  typen,
  chips,
  sortLabel,
  sortOptionen,
  ansichten = [],
}: {
  zielId: string;
  typen: StickyLink[];
  chips: StickyLink[];
  sortLabel: string;
  sortOptionen: StickyLink[];
  ansichten?: StickyLink[];
}) {
  const [sichtbar, setSichtbar] = useState(false);

  useEffect(() => {
    const ziel = document.getElementById(zielId);
    if (!ziel) return;
    const beobachter = new IntersectionObserver(
      ([eintrag]) => setSichtbar(!eintrag.isIntersecting && eintrag.boundingClientRect.top < 0),
      { threshold: 0 },
    );
    beobachter.observe(ziel);
    return () => beobachter.disconnect();
  }, [zielId]);

  const zurFilterleiste = () => {
    const ziel = document.getElementById(zielId);
    if (!ziel) return;
    window.scrollTo({ top: ziel.getBoundingClientRect().top + window.scrollY - 8, behavior: "smooth" });
    // Der Knopf wird gleich inert (Leiste verschwindet) – Fokus in die große Filterleiste mitnehmen
    ziel.focus({ preventScroll: true });
  };

  return (
    <div className={`gd-sticky ${sichtbar ? "gd-sticky--an" : ""}`} aria-hidden={!sichtbar} inert={!sichtbar}>
      <div className="gd-sticky__innen container">
        <div className="gd-sticky__typen">
          {typen.map((t) => (
            <Link key={t.label} href={t.href} scroll={false} className={`gd-chip ${t.aktiv ? "gd-chip--an" : ""}`} aria-current={t.aktiv || undefined}>
              {t.icon && <span className="icon" aria-hidden>{t.icon}</span>}
              {t.label}
            </Link>
          ))}
        </div>
        {chips.length > 0 && <span className="gd-trenner gd-trenner--hoch" aria-hidden />}
        <div className="gd-sticky__chips">
          {chips.map((c) => (
            <Link key={c.label} href={c.href} scroll={false} className="gd-chip gd-chip--an gd-chip--entfernen" aria-label={`Filter ${c.label} entfernen`}>
              {c.label}
              <span className="icon" aria-hidden>close</span>
            </Link>
          ))}
        </div>
        <button type="button" className="gd-filterknopf" onClick={zurFilterleiste}>
          <span className="icon" aria-hidden>tune</span>
          Filter
          {chips.length > 0 && <span className="gd-filterknopf__zahl">{chips.length}</span>}
        </button>
        <details className="gd-sort gd-sticky__sort">
          <summary>
            <span className="icon muted" aria-hidden>sort</span>
            <span className="gd-sort__label muted">Sortieren:</span>
            <b>{sortLabel}</b>
            <span className="icon" aria-hidden>expand_more</span>
          </summary>
          <div className="gd-menue gd-menue--rechts">
            {sortOptionen.map((s) => (
              <Link key={s.label} href={s.href} scroll={false} className={s.aktiv ? "is-aktiv" : ""}>{s.label}</Link>
            ))}
          </div>
        </details>
        {ansichten.length > 0 && (
          <div className="gd-umschalter gd-sticky__ansicht" role="group" aria-label="Ansicht">
            {ansichten.map((a) => (
              <Link key={a.label} href={a.href} scroll={false} className={a.aktiv ? "is-aktiv" : ""} aria-current={a.aktiv || undefined}>
                {a.icon && <span className="icon" aria-hidden>{a.icon}</span>}
                <span className="gd-umschalter__label">{a.label}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
