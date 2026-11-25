"use client";
// „Frisch aus der Redaktion“ (Magazin-Übersicht, 25.11.2026): Filter-Pillen je Rubrik und Karten-Raster. Alle Karten
// stehen schon im HTML (Server-Rendering, gut für Suchmaschinen); der Filter blendet im Browser nur aus.
// Die erste Karte der aktuellen Auswahl ist breit (Bild links, Text rechts), der Rest im Raster.
import Link from "next/link";
import { useState } from "react";
import type { KarteDaten } from "@/lib/magazin-uebersicht";

type Pille = { rubrik: string; name: string; icon: string };

export function FrischAusDerRedaktion({ karten, pillen }: { karten: KarteDaten[]; pillen: Pille[] }) {
  const [aktiv, setAktiv] = useState<string>("alle");
  const gezeigt = aktiv === "alle" ? karten : karten.filter((k) => k.rubrik === aktiv);
  return (
    <>
      {pillen.length > 1 && (
        <div className="mzf-pillen" role="group" aria-label="Nach Rubrik filtern">
          <button type="button" className="mzf-pille" aria-pressed={aktiv === "alle"} onClick={() => setAktiv("alle")}>
            Alle
          </button>
          {pillen.map((p) => (
            <button key={p.rubrik} type="button" className="mzf-pille" aria-pressed={aktiv === p.rubrik} onClick={() => setAktiv(p.rubrik)}>
              <span className="icon" aria-hidden data-icon={p.icon} />
              {p.name}
            </button>
          ))}
        </div>
      )}
      <div className="mzf-raster" role="list" aria-live="polite">
        {gezeigt.map((k, i) => (
          <article key={k.id} className={i === 0 ? "mzf-karte mzf-karte--breit" : "mzf-karte"} role="listitem">
            <div className="mzf-karte__bild">
              {/* eslint-disable-next-line @next/next/no-img-element -- statische, bereits optimierte Dateien aus public/ */}
              <img src={k.bild} alt="" width={1200} height={675} loading={i < 2 ? "eager" : "lazy"} decoding="async" />
              {k.bildKi && <span className="mz-ki-marke">Symbolbild (KI-generiert)</span>}
            </div>
            <div className="mzf-karte__text">
              <span className="mzf-chip">{k.rubrikName}</span>
              <h3 className="mzf-karte__titel">
                <Link href={k.href}>{k.titel}</Link>
              </h3>
              {k.teaser && <p className="mzf-karte__teaser">{k.teaser}</p>}
              <span className="mzf-karte__meta">
                {k.datum ? `${k.datum} · ` : ""}
                {k.lesezeit} Min. Lesezeit
              </span>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}
