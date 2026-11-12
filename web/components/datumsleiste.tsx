"use client";
// Tagesleiste der Startseite: horizontal scrollbar mit Pfeilen. Der gewählte Tag (gold) wird beim Laden und nach jedem
// Wechsel in die Mitte gerollt – auch wenn er Wochen in der Zukunft liegt (Auftraggeber 12.11.2026).
import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

export interface LeistenTag {
  tag: string;
  wochentag: string; // „Heute“, „Mo“ …
  tagNr: number;
  anzahl: number;
  href: string;
  aktiv: boolean;
  monat?: string; // „Dez“ – nur am Monatsersten, damit klar ist, wo man ist
}

export function Datumsleiste({ tage, nachher }: { tage: LeistenTag[]; nachher?: ReactNode }) {
  const leiste = useRef<HTMLElement>(null);
  const [rand, setRand] = useState({ links: false, rechts: true });

  const randPruefen = useCallback(() => {
    const el = leiste.current;
    if (!el) return;
    setRand({ links: el.scrollLeft > 4, rechts: el.scrollLeft + el.clientWidth < el.scrollWidth - 4 });
  }, []);

  const aktiverTag = tage.find((t) => t.aktiv)?.tag;

  // Gewählten Tag in die Mitte rollen (nur die Leiste, nie die Seite)
  useEffect(() => {
    const el = leiste.current;
    if (!el) return;
    const aktiv = aktiverTag ? el.querySelector<HTMLElement>(`[data-tag="${aktiverTag}"]`) : null;
    // Position relativ zur Leiste (offsetLeft bezieht sich auf einen anderen Vorfahren)
    const lr = el.getBoundingClientRect();
    const ar = aktiv?.getBoundingClientRect();
    const ziel = ar ? el.scrollLeft + (ar.left - lr.left) - (lr.width - ar.width) / 2 : 0;
    el.scrollTo({ left: Math.max(0, ziel), behavior: el.dataset.bereit ? "smooth" : "auto" });
    el.dataset.bereit = "1";
    randPruefen();
  }, [aktiverTag, randPruefen]);

  useEffect(() => {
    const el = leiste.current;
    if (!el) return;
    el.addEventListener("scroll", randPruefen, { passive: true });
    window.addEventListener("resize", randPruefen);
    return () => {
      el.removeEventListener("scroll", randPruefen);
      window.removeEventListener("resize", randPruefen);
    };
  }, [randPruefen]);

  const blaettern = (richtung: 1 | -1) => {
    const el = leiste.current;
    if (el) el.scrollBy({ left: richtung * el.clientWidth * 0.8, behavior: "smooth" });
  };

  return (
    <div className="datumsleiste-huelle">
      <button type="button" className="datumsleiste__pfeil" onClick={() => blaettern(-1)} disabled={!rand.links} aria-label="Frühere Tage">
        <span className="icon" aria-hidden data-icon="chevron_left" />
      </button>
      <nav className="datumsleiste" aria-label="Tag wählen" ref={leiste}>
        {tage.map((t) => (
          <Link key={t.tag} data-tag={t.tag} href={t.href} aria-current={t.aktiv ? "true" : undefined} scroll={false}>
            <span className="datumsleiste__wt">{t.monat ? `${t.wochentag} · ${t.monat}` : t.wochentag}</span>
            <span className="datumsleiste__tag">{t.tagNr}</span>
            <span className="datumsleiste__anz">
              {t.anzahl}
              <span className="nur-desktop"> Events</span>
            </span>
          </Link>
        ))}
      </nav>
      <button type="button" className="datumsleiste__pfeil" onClick={() => blaettern(1)} disabled={!rand.rechts} aria-label="Spätere Tage">
        <span className="icon" aria-hidden data-icon="chevron_right" />
      </button>
      {nachher}
    </div>
  );
}
