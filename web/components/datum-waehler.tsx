"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { zeitraumKey } from "@/lib/datum";

const WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];

function tagStr(d: Date): string {
  const j = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const t = String(d.getDate()).padStart(2, "0");
  return `${j}-${m}-${t}`;
}

interface Props {
  heute: string;
  ziel?: string;
  onWahl?: () => void;
  /** Weitere URL-Parameter, die beim Wählen erhalten bleiben (z.B. aktive Filter auf /entdecken) */
  parameter?: Record<string, string>;
  /** Aktuell gewähltes Datum (YYYY-MM-DD) – wird markiert, der Kalender öffnet in seinem Monat */
  gewaehlt?: string;
  /** Umschalter „Tag wählen“ / „Zeitraum wählen“ anzeigen (Startseite) */
  mitZeitraum?: boolean;
  /** Aktuell gewählter Zeitraum (von ≠ bis) – im Zeitraum-Modus markiert */
  zeitraum?: { von: string; bis: string };
}

type Modus = "tag" | "zeitraum";

export function DatumWaehler({ heute, ziel = "/entdecken", onWahl, parameter, gewaehlt, mitZeitraum = false, zeitraum }: Props) {
  const router = useRouter();
  const heuteDate = new Date(heute + "T00:00:00");
  const maxDate = new Date(heuteDate);
  maxDate.setDate(maxDate.getDate() + 59);
  const istZeitraum = !!zeitraum && zeitraum.von !== zeitraum.bis;
  const startTag = istZeitraum ? zeitraum!.von : gewaehlt;
  const start = startTag && /^\d{4}-\d{2}-\d{2}$/.test(startTag) ? new Date(startTag + "T00:00:00") : heuteDate;

  const [monat, setMonat] = useState(start.getMonth());
  const [jahr, setJahr] = useState(start.getFullYear());
  const [modus, setModus] = useState<Modus>(mitZeitraum && istZeitraum ? "zeitraum" : "tag");
  // Zeitraum-Auswahl in Arbeit: erster Klick = Start, zweiter Klick = Ende (wie bei einer Hotelsuche)
  const [anfang, setAnfang] = useState<string | null>(null);
  const [zeiger, setZeiger] = useState<string | null>(null);

  const ersterTag = new Date(jahr, monat, 1);
  const wochentagErster = (ersterTag.getDay() + 6) % 7;
  const tageImMonat = new Date(jahr, monat + 1, 0).getDate();

  function naechsterMonat() {
    if (monat === 11) { setMonat(0); setJahr(jahr + 1); }
    else setMonat(monat + 1);
  }
  function vorherigerMonat() {
    if (monat === 0) { setMonat(11); setJahr(jahr - 1); }
    else setMonat(monat - 1);
  }

  const kannZurueck = !(jahr === heuteDate.getFullYear() && monat === heuteDate.getMonth());
  const kannVor = !(jahr === maxDate.getFullYear() && monat > maxDate.getMonth());

  function oeffnen(datum: string, ereignis: React.MouseEvent<HTMLButtonElement>) {
    const qs = new URLSearchParams(parameter);
    qs.set("datum", datum);
    // Steckt der Kalender in einem aufklappbaren Menü (<details>), dieses schließen
    ereignis.currentTarget.closest("details")?.removeAttribute("open");
    router.push(`${ziel}?${qs.toString()}`);
    onWahl?.();
  }

  function tagKlick(str: string, ereignis: React.MouseEvent<HTMLButtonElement>) {
    if (modus === "tag") return oeffnen(str, ereignis);
    // Zeitraum: erster Klick setzt den Start; ein Klick davor setzt den Start neu; sonst ist es das Ende
    if (!anfang || str < anfang) {
      setAnfang(str);
      return;
    }
    oeffnen(zeitraumKey(anfang, str), ereignis);
  }

  function modusWechseln(m: Modus) {
    setModus(m);
    setAnfang(null);
    setZeiger(null);
  }

  // Markierter Bereich im Zeitraum-Modus: laufende Auswahl (Start bis Zeiger) oder der schon gewählte Zeitraum
  const bereich: { von: string; bis: string } | null =
    modus !== "zeitraum" ? null
      : anfang ? { von: anfang, bis: zeiger && zeiger > anfang ? zeiger : anfang }
      : istZeitraum ? zeitraum! : null;

  const zellen: (number | null)[] = [];
  for (let i = 0; i < wochentagErster; i++) zellen.push(null);
  for (let i = 1; i <= tageImMonat; i++) zellen.push(i);

  return (
    <div className="kalender">
      {mitZeitraum && (
        <>
          <div className="kalender__modus" role="group" aria-label="Auswahl">
            {([["tag", "Tag wählen"], ["zeitraum", "Zeitraum wählen"]] as const).map(([m, text]) => (
              <button key={m} type="button" className={modus === m ? "is-aktiv" : ""} aria-pressed={modus === m} onClick={() => modusWechseln(m)}>
                {text}
              </button>
            ))}
          </div>
          {modus === "zeitraum" && (
            <p className="kalender__hinweis" aria-live="polite">{anfang ? "Jetzt das Enddatum wählen" : "Startdatum wählen"}</p>
          )}
        </>
      )}
      <div className="kalender__kopf">
        <button type="button" className="kalender__pfeil" onClick={vorherigerMonat} disabled={!kannZurueck} aria-label="Vorheriger Monat">
          <span className="icon" aria-hidden data-icon="chevron_left" />
        </button>
        <span className="kalender__monat">{MONATE[monat]} {jahr}</span>
        <button type="button" className="kalender__pfeil" onClick={naechsterMonat} disabled={!kannVor} aria-label="Nächster Monat">
          <span className="icon" aria-hidden data-icon="chevron_right" />
        </button>
      </div>
      <div className="kalender__wt">
        {WT.map((w) => <span key={w}>{w}</span>)}
      </div>
      <div className="kalender__tage" onMouseLeave={() => setZeiger(null)}>
        {zellen.map((tag, i) => {
          if (tag === null) return <span key={`leer-${i}`} />;
          const d = new Date(jahr, monat, tag);
          const str = tagStr(d);
          const vergangen = str < heute;
          const zuWeit = d > maxDate;
          const istHeute = str === heute;
          const istGewaehlt = modus === "tag" && str === gewaehlt;
          const imBereich = !!bereich && str >= bereich.von && str <= bereich.bis;
          const klassen = [
            "kalender__tag",
            istHeute && "kalender__tag--heute",
            istGewaehlt && "kalender__tag--gewaehlt",
            imBereich && "kalender__tag--im-zeitraum",
            bereich && str === bereich.von && "kalender__tag--zeitraum-start",
            bereich && str === bereich.bis && "kalender__tag--zeitraum-ende",
          ].filter(Boolean).join(" ");
          return (
            <button
              key={tag}
              type="button"
              className={klassen}
              disabled={vergangen || zuWeit}
              aria-pressed={istGewaehlt || imBereich || undefined}
              onMouseEnter={() => anfang && setZeiger(str)}
              onClick={(e) => tagKlick(str, e)}
            >
              {tag}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Kalender der Startseite (Desktop neben der Tagesleiste, sonst als Pille „Kalender öffnen“ bei den Schnellfiltern).
 * Umschalter „Tag wählen“ / „Zeitraum wählen“; `gewaehlt` bzw. `zeitraum` ist gold markiert, „heute“ trägt einen
 * blauen Ring (Auftraggeber 16.11.2026). Unter 1200 px öffnet er mittig über einer Abdunklung; Tippen daneben oder
 * Escape schließt ihn.
 */
export function KalenderToggle({ heute, ziel, gewaehlt, zeitraum, klasse = "" }: {
  heute: string; ziel?: string; gewaehlt?: string; zeitraum?: { von: string; bis: string }; klasse?: string;
}) {
  const [offen, setOffen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!offen) return;
    const draussen = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOffen(false);
    };
    const taste = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOffen(false);
    };
    document.addEventListener("mousedown", draussen);
    document.addEventListener("keydown", taste);
    return () => {
      document.removeEventListener("mousedown", draussen);
      document.removeEventListener("keydown", taste);
    };
  }, [offen]);

  return (
    <div className={`kalender-toggle ${klasse}`} ref={ref}>
      <button type="button" className="chip chip--navy kalender-toggle__knopf" onClick={() => setOffen(!offen)} aria-label={offen ? "Kalender schließen" : "Kalender öffnen"} aria-expanded={offen}>
        <span className="icon kalender-toggle__icon" aria-hidden data-icon="calendar_month" />
        {/* Desktop „Kalender“, mobil „Kalender öffnen“ (Pille in der Reihe der Schnellfilter, Auftraggeber 16.11.2026) */}
        <span className="kalender-toggle__text kalender-toggle__text--gross">{offen ? "Schließen" : "Kalender"}</span>
        <span className="kalender-toggle__text kalender-toggle__text--mobil">{offen ? "Schließen" : "Kalender öffnen"}</span>
      </button>
      {offen && (
        <>
          <div className="kalender-hintergrund" aria-hidden onClick={() => setOffen(false)} />
          <div className="kalender-dropdown" role="dialog" aria-label="Datum wählen">
            <DatumWaehler heute={heute} ziel={ziel} gewaehlt={gewaehlt} zeitraum={zeitraum} mitZeitraum onWahl={() => setOffen(false)} />
          </div>
        </>
      )}
    </div>
  );
}

export function PopoverKalender({ heute, ziel }: { heute: string; ziel?: string }) {
  const [offen, setOffen] = useState(false);
  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        className="popover-kalender-btn"
        onClick={() => setOffen(!offen)}
      >
        <span className="icon" style={{ fontSize: 16 }} aria-hidden data-icon="calendar_month" />
        Exaktes Datum
        <span className="icon" style={{ fontSize: 16 }} aria-hidden data-icon={offen ? "expand_less" : "expand_more"} />
      </button>
      {offen && (
        <div className="popover-kalender">
          <DatumWaehler heute={heute} ziel={ziel} onWahl={() => setOffen(false)} />
        </div>
      )}
    </div>
  );
}

const ZEITRAUM_LINKS = [
  { key: "heute", label: "Heute" },
  { key: "morgen", label: "Morgen" },
  { key: "wochenende", label: "Dieses Wochenende" },
  { key: "woche", label: "Diese Woche" },
  { key: "monat", label: "Nächste 30 Tage" },
  { key: "alle", label: "60 Tage" },
];

const keinAbo = () => () => {};

function heuteLokal(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
}

export function DatumPill() {
  const [offen, setOffen] = useState(false);
  const [kalender, setKalender] = useState(false);
  // Heutiges Datum erst im Browser (Server liefert ""), ohne setState im Effect
  const heute = useSyncExternalStore(keinAbo, heuteLokal, () => "");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!offen) return;
    function schliessen(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOffen(false);
        setKalender(false);
      }
    }
    document.addEventListener("mousedown", schliessen);
    return () => document.removeEventListener("mousedown", schliessen);
  }, [offen]);

  return (
    <div className="datum-pill" ref={ref}>
      <button type="button" className="datum-pill__btn" onClick={() => { setOffen(!offen); setKalender(false); }}>
        <span className="icon" style={{ fontSize: 16 }} aria-hidden data-icon="calendar_today" />
        Heute
        <span className="icon" style={{ fontSize: 16 }} aria-hidden data-icon={offen ? "expand_less" : "expand_more"} />
      </button>
      {offen && heute && (
        <div className="popover">
          {ZEITRAUM_LINKS.map((z) => (
            <Link key={z.key} href={`/entdecken?datum=${z.key}`} onClick={() => { setOffen(false); setKalender(false); }}>
              {z.label}
            </Link>
          ))}
          <div style={{ position: "relative" }}>
            <button
              type="button"
              className="popover-kalender-btn"
              onClick={() => setKalender(!kalender)}
            >
              <span className="icon" style={{ fontSize: 16 }} aria-hidden data-icon="calendar_month" />
              Exaktes Datum
              <span className="icon" style={{ fontSize: 16 }} aria-hidden data-icon={kalender ? "expand_less" : "expand_more"} />
            </button>
            {kalender && (
              <div className="popover-kalender">
                <DatumWaehler heute={heute} ziel="/entdecken" onWahl={() => { setOffen(false); setKalender(false); }} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
