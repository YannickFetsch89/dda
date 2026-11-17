"use client";
// „Heute geöffnet?“ für den Weihnachtsmarkt-Guide (Plan E5): Server und Cache liefern nur einen neutralen Platzhalter,
// erst der Browser rechnet aus den Zeiten im ersten HTML (Europe/Berlin). So steht nie ein veralteter Zustand im Cache,
// und das Hydrieren stimmt (gleicher Platzhalter auf Server und Client beim ersten Rendern).
import { useEffect, useState } from "react";
import { heuteBerlin, minutenBerlin } from "@/lib/datum";
import { jetztText, oeffnungAm, oeffnungText, type Saisons, type Zustand } from "@/lib/weihnachtsmaerkte";

const PLATZHALTER = "Öffnungszeiten siehe unten";

export function WmZustand({ saisons, mitUhrzeit = false, className = "" }: { saisons: Saisons; mitUhrzeit?: boolean; className?: string }) {
  const [stand, setStand] = useState<{ text: string; zustand: Zustand } | null>(null);
  useEffect(() => {
    const rechnen = () => {
      const o = oeffnungAm(saisons, heuteBerlin());
      setStand({ text: mitUhrzeit ? jetztText(o, minutenBerlin()) : oeffnungText(o), zustand: o.zustand });
    };
    rechnen();
    const timer = window.setInterval(rechnen, 60_000);
    return () => window.clearInterval(timer);
  }, [saisons, mitUhrzeit]);
  return (
    <span className={`wm-zustand wm-zustand--${stand?.zustand ?? "laden"} ${className}`} aria-live="polite">
      <span className="wm-zustand__punkt" aria-hidden />
      {stand?.text ?? PLATZHALTER}
    </span>
  );
}
