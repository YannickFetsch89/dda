"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

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
}

export function DatumWaehler({ heute, ziel = "/entdecken", onWahl }: Props) {
  const router = useRouter();
  const heuteDate = new Date(heute + "T00:00:00");
  const maxDate = new Date(heuteDate);
  maxDate.setDate(maxDate.getDate() + 59);

  const [monat, setMonat] = useState(heuteDate.getMonth());
  const [jahr, setJahr] = useState(heuteDate.getFullYear());

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

  function tagKlick(tag: number) {
    const d = new Date(jahr, monat, tag);
    const str = tagStr(d);
    router.push(`${ziel}?datum=${str}`);
    onWahl?.();
  }

  const zellen: (number | null)[] = [];
  for (let i = 0; i < wochentagErster; i++) zellen.push(null);
  for (let i = 1; i <= tageImMonat; i++) zellen.push(i);

  return (
    <div className="kalender">
      <div className="kalender__kopf">
        <button type="button" className="kalender__pfeil" onClick={vorherigerMonat} disabled={!kannZurueck} aria-label="Vorheriger Monat">
          <span className="icon">chevron_left</span>
        </button>
        <span className="kalender__monat">{MONATE[monat]} {jahr}</span>
        <button type="button" className="kalender__pfeil" onClick={naechsterMonat} disabled={!kannVor} aria-label="Nächster Monat">
          <span className="icon">chevron_right</span>
        </button>
      </div>
      <div className="kalender__wt">
        {WT.map((w) => <span key={w}>{w}</span>)}
      </div>
      <div className="kalender__tage">
        {zellen.map((tag, i) => {
          if (tag === null) return <span key={`leer-${i}`} />;
          const d = new Date(jahr, monat, tag);
          const str = tagStr(d);
          const vergangen = str < heute;
          const zuWeit = d > maxDate;
          const istHeute = str === heute;
          return (
            <button
              key={tag}
              type="button"
              className={`kalender__tag ${istHeute ? "kalender__tag--heute" : ""}`}
              disabled={vergangen || zuWeit}
              onClick={() => tagKlick(tag)}
            >
              {tag}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function KalenderToggle({ heute, ziel }: { heute: string; ziel?: string }) {
  const [offen, setOffen] = useState(false);
  return (
    <div className="kalender-toggle">
      <button type="button" className="chip chip--navy" onClick={() => setOffen(!offen)}>
        <span className="icon" style={{ fontSize: 16 }}>calendar_month</span>
        {offen ? "Schließen" : "Kalender"}
      </button>
      {offen && (
        <div className="kalender-dropdown">
          <DatumWaehler heute={heute} ziel={ziel} onWahl={() => setOffen(false)} />
        </div>
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
        <span className="icon" style={{ fontSize: 16 }}>calendar_month</span>
        Exaktes Datum
        <span className="icon" style={{ fontSize: 16 }}>{offen ? "expand_less" : "expand_more"}</span>
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

function heuteLokal(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
}

export function DatumPill() {
  const [offen, setOffen] = useState(false);
  const [kalender, setKalender] = useState(false);
  const [heute, setHeute] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => { setHeute(heuteLokal()); }, []);

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
        <span className="icon" style={{ fontSize: 16 }}>calendar_today</span>
        Heute
        <span className="icon" style={{ fontSize: 16 }}>{offen ? "expand_less" : "expand_more"}</span>
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
              <span className="icon" style={{ fontSize: 16 }}>calendar_month</span>
              Exaktes Datum
              <span className="icon" style={{ fontSize: 16 }}>{kalender ? "expand_less" : "expand_more"}</span>
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
