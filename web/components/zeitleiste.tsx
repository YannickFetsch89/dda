"use client";
// Timeline des Tagesplaners. Client Component, weil der Jetzt-Marker die aktuelle Uhrzeit braucht.
import Link from "next/link";
import { useEffect, useState } from "react";
import { BildImg } from "./client";
import { katStil, kategorie } from "@/lib/kategorien";
import { minutenBerlin } from "@/lib/datum";
import { symbolbild } from "@/lib/symbolbild";
import { eventBildUrl } from "@/lib/bilder";
import { eventPfad } from "@/lib/pfade";
import type { DddEvent } from "@/lib/typen";
import { zeitKurz } from "@/lib/termine";

export interface Abschnitt {
  name: string;
  bereich: string;
  icon: string;
  von: number; // Minuten seit Mitternacht
  bis: number;
  events: DddEvent[];
}

/** Minuten eines Tages ab 6 Uhr gerechnet: Zeiten vor 6 Uhr gehören zur Nacht davor (00:30 → 24:30 = 1470). */
export function tagesminuten(minuten: number): number {
  return minuten < 6 * 60 ? minuten + 24 * 60 : minuten;
}

function zuMinuten(z: string): number {
  const [h, m] = z.split(":").map(Number);
  return tagesminuten(h * 60 + m);
}

/**
 * Uhrzeit eines Eintrags innerhalb des Abschnitts: Bei gebündelten Terminen (11:00 und 19:00)
 * zählt im Abschnitt „Abends“ 19:00 – für den Jetzt-Marker und die angezeigte Zeit.
 */
function zeitImAbschnitt(e: DddEvent, a: Pick<Abschnitt, "von" | "bis">): string | null {
  const zeiten = e.uhrzeiten ?? (e.uhrzeit ? [e.uhrzeit] : []);
  return zeiten.find((z) => zuMinuten(z) >= a.von && zuMinuten(z) < a.bis) ?? zeiten[0] ?? null;
}

function minuten(e: DddEvent, a: Pick<Abschnitt, "von" | "bis">): number {
  const z = zeitImAbschnitt(e, a);
  return z ? zuMinuten(z) : -1;
}

function Zeile({ e, abschnitt }: { e: DddEvent; abschnitt: Pick<Abschnitt, "von" | "bis"> }) {
  const k = kategorie(e.kategorie);
  // Im Abschnitt die passende Uhrzeit zeigen; „Ganztägig“ (von = -1) bleibt ohne Zeit
  const zeit = e.uhrzeiten && abschnitt.von >= 0 ? zeitImAbschnitt(e, abschnitt) : zeitKurz(e);
  return (
    <div className="tl">
      <span className="tl__zeit">{zeit && /^\d{2}:\d{2}$/.test(zeit) ? <time dateTime={`${e.datum}T${zeit}`}>{zeit}</time> : (zeit ?? "")}</span>
      <span className="tl__linie">
        <span className="punkt" style={katStil(e.kategorie)} />
      </span>
      <article className="tl__karte">
        <div className={`bild ${e.abgesagt ? "bild--abgesagt" : ""}`} style={katStil(e.kategorie)}>
          <BildImg src={eventBildUrl(e)} ersatz={symbolbild(e)} alt="" icon={k.icon} />
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
            {/* Kanonische URL direkt – nicht /event/<uuid> (das ist nur noch eine 308-Weiterleitung) */}
            <Link href={eventPfad(e)}>{e.titel}</Link>
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
  // Für Vergleiche mit den Abschnitten ebenfalls in Tagesminuten (01:00 nachts → 25:00)
  const jetztTag = jetzt === null ? null : tagesminuten(jetzt);

  return (
    <>
      {abschnitte.map((a) => {
        const markerHier = jetztTag !== null && jetztTag >= a.von && jetztTag < a.bis;
        if (!a.events.length && !markerHier) return null;
        const vorher = markerHier ? a.events.filter((e) => minuten(e, a) <= jetztTag!) : a.events;
        const nachher = markerHier ? a.events.filter((e) => minuten(e, a) > jetztTag!) : [];
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
              <Zeile key={e.id} e={e} abschnitt={a} />
            ))}
            {markerHier && <Jetzt zeit={jetztText} />}
            {nachher.map((e) => (
              <Zeile key={e.id} e={e} abschnitt={a} />
            ))}
          </section>
        );
      })}
    </>
  );
}
