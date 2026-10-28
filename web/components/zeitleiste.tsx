"use client";
// Timeline des Tagesplaners. Client Component, weil der Jetzt-Marker die aktuelle Uhrzeit braucht.
import Link from "next/link";
import { useEffect, useState } from "react";
import { BildImg } from "./client";
import { katStil, kategorie } from "@/lib/kategorien";
import { minutenBerlin } from "@/lib/datum";
import { symbolbild } from "@/lib/symbolbild";
import type { DddEvent } from "@/lib/typen";

export interface Abschnitt {
  name: string;
  bereich: string;
  icon: string;
  von: number; // Minuten seit Mitternacht
  bis: number;
  events: DddEvent[];
}

function minuten(e: DddEvent): number {
  if (!e.uhrzeit) return -1;
  const [h, m] = e.uhrzeit.split(":").map(Number);
  return h * 60 + m;
}

function Zeile({ e }: { e: DddEvent }) {
  const k = kategorie(e.kategorie);
  return (
    <div className="tl">
      <span className="tl__zeit">{e.uhrzeit ?? ""}</span>
      <span className="tl__linie">
        <span className="punkt" style={katStil(e.kategorie)} />
      </span>
      <article className="tl__karte">
        <div className={`bild ${e.abgesagt ? "bild--abgesagt" : ""}`} style={katStil(e.kategorie)}>
          <BildImg src={e.bild_url} ersatz={symbolbild(e)} alt="" icon={k.icon} />
          {e.abgesagt && <span className="abgesagt-tag bild__abgesagt">Abgesagt</span>}
        </div>
        <div className="tl__karte-text">
          <span className="katlabel" style={katStil(e.kategorie)}>
            <span className="icon" aria-hidden>
              {k.icon}
            </span>
            {k.name}
          </span>
          <h3 className="tl__titel">
            <Link href={`/event/${encodeURIComponent(e.id)}`}>{e.titel}</Link>
          </h3>
          <span className="tl__sub">
            {e.ort}
            {e.preis ? ` · ${e.preis}` : ""}
          </span>
        </div>
      </article>
    </div>
  );
}

function Jetzt({ zeit }: { zeit: string }) {
  return (
    <div className="tl tl--jetzt" aria-label={`Jetzt, ${zeit} Uhr`}>
      <span className="tl__zeit">{zeit}</span>
      <span className="tl__linie">
        <span className="punkt" />
      </span>
      <span className="jetzt-text">JETZT</span>
    </div>
  );
}

export function Zeitleiste({ abschnitte, istHeute }: { abschnitte: Abschnitt[]; istHeute: boolean }) {
  // Erst nach dem Mount setzen, damit Server- und Client-HTML übereinstimmen
  const [jetzt, setJetzt] = useState<number | null>(null);
  useEffect(() => {
    if (!istHeute) return;
    const aktualisieren = () => setJetzt(minutenBerlin());
    aktualisieren();
    const t = setInterval(aktualisieren, 60_000);
    return () => clearInterval(t);
  }, [istHeute]);

  const jetztText = jetzt === null ? "" : `${String(Math.floor(jetzt / 60)).padStart(2, "0")}:${String(jetzt % 60).padStart(2, "0")}`;

  return (
    <>
      {abschnitte.map((a) => {
        const markerHier = jetzt !== null && jetzt >= a.von && jetzt < a.bis;
        if (!a.events.length && !markerHier) return null;
        const vorher = markerHier ? a.events.filter((e) => minuten(e) <= jetzt!) : a.events;
        const nachher = markerHier ? a.events.filter((e) => minuten(e) > jetzt!) : [];
        return (
          <section key={a.name} className="tagesabschnitt">
            <div className="tagesabschnitt__kopf">
              <span className="icon" aria-hidden>
                {a.icon}
              </span>
              <h2 className="d">{a.name}</h2>
              <span>{a.bereich}</span>
            </div>
            {vorher.map((e) => (
              <Zeile key={e.id} e={e} />
            ))}
            {markerHier && <Jetzt zeit={jetztText} />}
            {nachher.map((e) => (
              <Zeile key={e.id} e={e} />
            ))}
          </section>
        );
      })}
    </>
  );
}
