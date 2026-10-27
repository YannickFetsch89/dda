"use client";
// Merkliste: IDs aus localStorage, Events über /api/events
import Link from "next/link";
import { useEffect, useState } from "react";
import { useMerkliste } from "./client";
import { EventKarte, Leer, SkeletonKarten } from "./karten";
import type { DddEvent } from "@/lib/typen";

type Zustand = { status: "laden" } | { status: "fehler" } | { status: "fertig"; heute: string; events: DddEvent[] };

export function MerklisteInhalt() {
  const ids = useMerkliste();
  const schluessel = ids.join(",");
  const [zustand, setZustand] = useState<Zustand>({ status: "laden" });
  const [versuch, setVersuch] = useState(0);

  useEffect(() => {
    if (!schluessel) return;
    let abgebrochen = false;
    fetch(`/api/events?ids=${encodeURIComponent(schluessel)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((daten: { heute: string; events: DddEvent[] }) => {
        if (!abgebrochen) setZustand({ status: "fertig", heute: daten.heute, events: daten.events });
      })
      .catch(() => {
        if (!abgebrochen) setZustand({ status: "fehler" });
      });
    return () => {
      abgebrochen = true;
    };
  }, [schluessel, versuch]);

  if (!ids.length) {
    return (
      <Leer titel="Noch nichts gemerkt.">
        <span>Tipp aufs Herz, dann landet ein Event hier.</span>
        <Link href="/entdecken" className="link">
          Events entdecken
        </Link>
      </Leer>
    );
  }
  if (zustand.status === "laden") return <SkeletonKarten anzahl={Math.min(ids.length, 8)} />;
  if (zustand.status === "fehler") {
    return (
      <div className="status status--fehler" role="alert">
        <span className="icon">error</span>
        <div>
          Die Merkliste konnte nicht geladen werden.{" "}
          <button type="button" className="link" onClick={() => setVersuch((v) => v + 1)} style={{ color: "inherit", textDecoration: "underline" }}>
            Nochmal versuchen
          </button>
        </div>
      </div>
    );
  }

  // Reihenfolge: kommende zuerst, nach Datum
  const sichtbar = zustand.events.filter((e) => ids.includes(e.id)).sort((a, b) => a.datum.localeCompare(b.datum));
  const fehlend = ids.length - sichtbar.length;
  return (
    <>
      {sichtbar.length > 0 ? (
        <div className="raster" role="list">
          {sichtbar.map((e) => (
            <EventKarte key={e.id} e={e} heute={zustand.heute} variante="grid" />
          ))}
        </div>
      ) : (
        <Leer titel="Deine gemerkten Events sind vorbei." />
      )}
      {fehlend > 0 && (
        <p className="zuordnungs-hinweis" style={{ marginTop: 16 }}>
          {fehlend} gemerkte{fehlend === 1 ? "s Event ist" : " Events sind"} nicht mehr verfügbar.
        </p>
      )}
    </>
  );
}
