"use client";
// Lädt die Kartenansicht (MapLibre, ~1 MB) erst, wenn sie wirklich angezeigt wird – nicht im normalen Grid.
import dynamic from "next/dynamic";
import type { KartenOrt } from "./guide-karte";

const GuideKarte = dynamic(() => import("./guide-karte"), {
  ssr: false,
  loading: () => <div className="gd-kartenansicht gd-kartenansicht--laedt" aria-busy="true">Karte wird geladen …</div>,
});

export function GuideKarteLazy({ orte }: { orte: KartenOrt[] }) {
  return <GuideKarte orte={orte} />;
}
