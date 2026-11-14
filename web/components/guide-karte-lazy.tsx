"use client";
// Kartenansicht der Guides – lädt zwei Dinge erst im Browser und parallel:
//  1. die Kartenbibliothek (MapLibre, ~1 MB) – nur, wenn die Karte wirklich angezeigt wird
//  2. die Kartenpunkte über /api/guide-karte (bei Restaurants über 600) – statt sie in die erste
//     HTML-Antwort zu packen, die dadurch vorher über 1 MB groß war und auf dem Handy lange lud.
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import type { KartenOrt } from "./guide-karte";

const GuideKarte = dynamic(() => import("./guide-karte"), {
  ssr: false,
  loading: () => <div className="gd-kartenansicht gd-kartenansicht--laedt" aria-busy="true">Karte wird geladen …</div>,
});

type Stand = { quelle: string; orte: KartenOrt[] | null; fehler: boolean };

/** `quelle`: Adresse der Kartenpunkte mit den aktuellen Filtern, z. B. /api/guide-karte?hub=restaurants&stadtteil=bilk */
export function GuideKarteLazy({ quelle, naehe = false }: { quelle: string; naehe?: boolean }) {
  const [stand, setStand] = useState<Stand | null>(null);

  useEffect(() => {
    let abgebrochen = false;
    fetch(quelle)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((orte: KartenOrt[]) => { if (!abgebrochen) setStand({ quelle, orte, fehler: false }); })
      .catch(() => { if (!abgebrochen) setStand({ quelle, orte: [], fehler: true }); });
    return () => { abgebrochen = true; };
  }, [quelle]);

  // Gehört der Stand zu einer älteren Filter-URL, gilt die Karte als „lädt“
  const aktuell = stand?.quelle === quelle ? stand : null;
  return <GuideKarte orte={aktuell?.orte ?? null} ladefehler={aktuell?.fehler ?? false} naehe={naehe} />;
}
