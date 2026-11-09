"use client";
// Fragebogen „Was dürfen wir dir empfehlen?“ für den Restaurant-Hub.
//
// Beim Aufruf ohne Filter steht er als fester Bereich unter dem Hero – Teil der Seite, keine
// Einblendung über dem Inhalt (Google wertet verdeckende Interstitials nach dem Klick aus der Suche ab).
// Der Server rendert ihn mit (kein Nachladen, erste Frage steht im HTML); Karte und Liste folgen darunter.
// Das X klappt ihn zu. „Empfehlung finden“ im Hero öffnet ihn als Vollbild-Dialog (vom Nutzer
// ausgelöst – unkritisch). Nach der letzten Frage geht es auf die passend gefilterte Hub-URL.
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Icon } from "./karten";
import { ALLE_TYPEN, SEITE, filterHref, preisZeichen, type OrtTyp } from "@/lib/guide-filter";

/** Kompakte Daten für Live-Zählwerte: Nachschlagetabellen + ein Tupel je Ort. */
export interface FragebogenDaten {
  stadtteile: { slug: string; name: string }[];
  kuechen: { slug: string; name: string }[];
  tags: { slug: string; name: string }[];
  /** [Typ-Index in ALLE_TYPEN, Stadtteil-Index (-1), Küchen-Index (-1), Preisstufe 0–3, Tag-Bitmaske] */
  orte: [number, number, number, number, number][];
}

type Schritt = "art" | "ort" | "lust" | "wichtig" | "preis";
type Variante = "inline" | "dialog";

interface Antworten {
  typen: OrtTyp[];
  stadtteil: number | null; // null = überall
  kuechen: number[];
  tags: number[];
  preise: number[];
}

const LEER: Antworten = { typen: [], stadtteil: null, kuechen: [], tags: [], preise: [] };
const EREIGNIS = "ddd-fragebogen-oeffnen";

const ARTEN: { label: string; text: string; icon: string; typen: OrtTyp[] }[] = [
  { label: "Restaurants", text: "Richtig essen gehen", icon: "restaurant", typen: ["restaurant"] },
  { label: "Cafés", text: "Kaffee, Kuchen, Frühstück", icon: "local_cafe", typen: ["cafe"] },
  { label: "Schnellimbiss", text: "Schnell und unkompliziert", icon: "lunch_dining", typen: ["imbiss"] },
  { label: "Alles", text: "Überrascht mich", icon: "auto_awesome", typen: [...ALLE_TYPEN] },
];

/** Knopf im Hero: öffnet den Fragebogen (Dialog bzw. springt zum offenen Bereich). */
export function FragebogenKnopf() {
  return (
    <button type="button" className="fb-start" onClick={() => window.dispatchEvent(new Event(EREIGNIS))}>
      <Icon name="auto_awesome" />Empfehlung finden
    </button>
  );
}

export function Fragebogen({ basis, daten, start }: { basis: string; daten: FragebogenDaten; start: boolean }) {
  const router = useRouter();
  const dialog = useRef<HTMLDialogElement>(null);
  const bereich = useRef<HTMLElement>(null);
  const [inlineOffen, setInlineOffen] = useState(true);
  const [dialogOffen, setDialogOffen] = useState(false);
  const [schritt, setSchritt] = useState<Schritt>("art");
  const [a, setA] = useState<Antworten>(LEER);
  // Fester Bereich nur auf der ungefilterten Hub-Seite
  const inlineSichtbar = start && inlineOffen && !dialogOffen;

  // „Empfehlung finden“: offenen Bereich ansteuern, sonst als Dialog öffnen
  useEffect(() => {
    const oeffnen = () => {
      if (start && inlineOffen) {
        bereich.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        bereich.current?.querySelector<HTMLElement>("h2")?.focus({ preventScroll: true });
        return;
      }
      setA(LEER);
      setSchritt("art");
      setDialogOffen(true);
      dialog.current?.showModal();
    };
    window.addEventListener(EREIGNIS, oeffnen);
    return () => window.removeEventListener(EREIGNIS, oeffnen);
  }, [start, inlineOffen]);

  const nurCafes = a.typen.length === 1 && a.typen[0] === "cafe";
  const schritte: Schritt[] = ["art", "ort", nurCafes ? "wichtig" : "lust", "preis"];
  const nummer = schritte.indexOf(schritt) + 1;

  /** Orte, die zu den Antworten passen (rund 700 Tupel – ohne eigenes Memo schnell genug). */
  const passend = (ant: Antworten) =>
    daten.orte.filter(([t, s, k, p, g]) => {
      if (ant.typen.length && !ant.typen.includes(ALLE_TYPEN[t])) return false;
      if (ant.stadtteil !== null && s !== ant.stadtteil) return false;
      if (ant.kuechen.length && !ant.kuechen.includes(k)) return false;
      if (ant.tags.some((i) => !(g & (1 << i)))) return false;
      if (ant.preise.length && !ant.preise.includes(p)) return false;
      return true;
    });

  const treffer = passend(a).length;

  function dialogSchliessen() {
    dialog.current?.close();
    setDialogOffen(false);
  }

  function bereichSchliessen() {
    setInlineOffen(false);
    // Fokus auf die Filterleiste, damit Tastatur- und Screenreader-Nutzer nicht „ins Leere“ fallen
    document.getElementById("gd-filter")?.focus({ preventScroll: true });
  }

  function weiter(neu: Antworten) {
    setA(neu);
    const liste: Schritt[] = ["art", "ort", neu.typen.length === 1 && neu.typen[0] === "cafe" ? "wichtig" : "lust", "preis"];
    const naechster = liste[liste.indexOf(schritt) + 1];
    if (naechster) setSchritt(naechster);
  }

  function zurueck() {
    const vorher = schritte[schritte.indexOf(schritt) - 1];
    if (vorher) setSchritt(vorher);
  }

  function anzeigen() {
    const href = filterHref(basis, {
      typen: a.typen.length ? a.typen : [...ALLE_TYPEN],
      stadtteile: a.stadtteil !== null ? [daten.stadtteile[a.stadtteil].slug] : [],
      kuechen: a.kuechen.map((i) => daten.kuechen[i].slug),
      preise: a.preise,
      tags: a.tags.map((i) => daten.tags[i].slug),
      sort: "empfohlen",
      anzahl: SEITE,
      ansicht: "karte",
    }, {});
    dialogSchliessen();
    setInlineOffen(false);
    router.push(href);
  }

  const umschalten = (liste: number[], i: number) => (liste.includes(i) ? liste.filter((x) => x !== i) : [...liste, i]);

  /** Anzahl je Index (Stadtteil oder Küche) unter den passenden Orten, absteigend, nur mit Treffern. */
  const zaehlen = (orte: [number, number, number, number, number][], spalte: 1 | 2, namen: { name: string }[]) => {
    const z = new Map<number, number>();
    for (const o of orte) if (o[spalte] >= 0) z.set(o[spalte], (z.get(o[spalte]) ?? 0) + 1);
    return [...z.entries()].sort((x, y) => y[1] - x[1] || namen[x[0]].name.localeCompare(namen[y[0]].name, "de"));
  };
  const stadtteilZahlen = schritt === "ort" ? zaehlen(passend({ ...a, stadtteil: null, kuechen: [], tags: [], preise: [] }), 1, daten.stadtteile) : [];
  const kuechenZahlen = schritt === "lust" ? zaehlen(passend({ ...a, kuechen: [], tags: [], preise: [] }), 2, daten.kuechen) : [];

  /** Inhalt beider Varianten. Autofokus nur im Dialog – der feste Bereich stiehlt beim Laden keinen Fokus. */
  const panel = (v: Variante) => {
    const fokus = v === "dialog";
    const frageId = `fb-frage-${v}`;
    const titel = (text: string) => <h2 id={frageId} className="d" tabIndex={-1}>{text}</h2>;
    return (
      <>
        <div className="fb__kopf">
          {nummer > 1 ? (
            <button type="button" className="fb__zurueck" onClick={zurueck}><Icon name="arrow_back" />Zurück</button>
          ) : v === "inline" ? <span className="fb__marke"><Icon name="auto_awesome" /><span className="fb__marke-text">Empfehlung finden</span></span> : <span />}
          <span className="fb__schritt" aria-hidden>Frage {nummer} von {schritte.length}</span>
          <button type="button" className="fb__x" onClick={v === "dialog" ? dialogSchliessen : bereichSchliessen}
            aria-label={v === "dialog" ? "Fragebogen schließen" : "Fragebogen zuklappen und alle Empfehlungen zeigen"}>
            <Icon name="close" />
          </button>
        </div>
        <div className="fb__fortschritt" aria-hidden><span style={{ width: `${(nummer / schritte.length) * 100}%` }} /></div>

        {schritt === "art" && (
          <div className="fb__inhalt">
            {titel("Was dürfen wir dir empfehlen?")}
            <div className="fb__karten">
              {ARTEN.map((art, i) => {
                const n = passend({ ...LEER, typen: art.typen }).length;
                return (
                  <button key={art.label} type="button" className="fb__karte" autoFocus={fokus && i === 0} disabled={!n}
                    onClick={() => weiter({ ...LEER, typen: art.typen })}>
                    <Icon name={art.icon} />
                    <b>{art.label}</b>
                    <span>{art.text}</span>
                    <span className="fb__zahl">{n.toLocaleString("de-DE")} Orte</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {schritt === "ort" && (
          <div className="fb__inhalt">
            {titel("Wo dürfen wir für dich suchen?")}
            <div className="fb__chips fb__chips--viele">
              <button type="button" className="gd-chip gd-chip--gross fb__chip--haupt" autoFocus={fokus}
                onClick={() => weiter({ ...a, stadtteil: null })}>
                <Icon name="explore" />Überall in Düsseldorf
              </button>
              {stadtteilZahlen.map(([i, n]) => (
                <button key={i} type="button" className="gd-chip gd-chip--gross" onClick={() => weiter({ ...a, stadtteil: i })}>
                  {daten.stadtteile[i].name}<span className="gd-chip__zahl">{n}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {schritt === "lust" && (
          <div className="fb__inhalt">
            {titel("Worauf hast du Lust?")}
            <p className="fb__hinweis">Eine oder mehrere Richtungen – oder einfach weiter.</p>
            <div className="fb__chips fb__chips--viele">
              {kuechenZahlen.map(([i, n]) => {
                const an = a.kuechen.includes(i);
                return (
                  <button key={i} type="button" className={`gd-chip gd-chip--gross ${an ? "gd-chip--an" : ""}`} aria-pressed={an}
                    onClick={() => setA({ ...a, kuechen: umschalten(a.kuechen, i) })}>
                    {an && <Icon name="check" />}{daten.kuechen[i].name}<span className="gd-chip__zahl">{n}</span>
                  </button>
                );
              })}
            </div>
            <div className="fb__fuss">
              <button type="button" className="fb__weiter" onClick={() => weiter(a)}>
                {a.kuechen.length ? "Weiter" : "Egal, weiter"}<Icon name="arrow_forward" />
              </button>
            </div>
          </div>
        )}

        {schritt === "wichtig" && (
          <div className="fb__inhalt">
            {titel("Was ist dir wichtig?")}
            <p className="fb__hinweis">Alles, was du wählst, muss das Café bieten.</p>
            <div className="fb__chips">
              {daten.tags.map((t, i) => {
                const an = a.tags.includes(i);
                const n = passend({ ...a, tags: an ? a.tags : [...a.tags, i] }).length;
                return (
                  <button key={t.slug} type="button" className={`gd-chip gd-chip--gross ${an ? "gd-chip--an" : ""}`} aria-pressed={an}
                    disabled={!an && !n} onClick={() => setA({ ...a, tags: umschalten(a.tags, i) })}>
                    {an && <Icon name="check" />}{t.name}<span className="gd-chip__zahl">{n}</span>
                  </button>
                );
              })}
            </div>
            <div className="fb__fuss">
              <button type="button" className="fb__weiter" onClick={() => weiter(a)}>
                {a.tags.length ? "Weiter" : "Egal, weiter"}<Icon name="arrow_forward" />
              </button>
            </div>
          </div>
        )}

        {schritt === "preis" && (
          <div className="fb__inhalt">
            {titel("Wie viel möchtest du ausgeben?")}
            <div className="fb__karten fb__karten--preis">
              {[1, 2, 3].map((p) => {
                const an = a.preise.includes(p);
                const n = passend({ ...a, preise: [p] }).length;
                return (
                  <button key={p} type="button" className={`fb__karte ${an ? "is-an" : ""}`} aria-pressed={an} disabled={!n}
                    onClick={() => setA({ ...a, preise: umschalten(a.preise, p) })}>
                    <b>{preisZeichen(p)}</b>
                    <span>{["Günstig", "Mittel", "Gehoben"][p - 1]}</span>
                    <span className="fb__zahl">{n} Orte</span>
                  </button>
                );
              })}
            </div>
            <div className="fb__fuss">
              <button type="button" className="fb__weiter fb__weiter--ziel" onClick={anzeigen} disabled={!treffer}>
                {treffer.toLocaleString("de-DE")} {treffer === 1 ? "Empfehlung" : "Empfehlungen"} anzeigen<Icon name="arrow_forward" />
              </button>
            </div>
          </div>
        )}

        {schritt !== "art" && schritt !== "preis" && (
          <p className="fb__stand" aria-live="polite">{treffer.toLocaleString("de-DE")} passende Orte</p>
        )}
      </>
    );
  };

  return (
    <>
      {inlineSichtbar && (
        <div className="container">
          <section ref={bereich} className="fb fb--inline" aria-labelledby="fb-frage-inline">
            {panel("inline")}
          </section>
        </div>
      )}

      <dialog
        ref={dialog}
        className="fb fb--dialog"
        aria-labelledby="fb-frage-dialog"
        onCancel={(e) => { e.preventDefault(); dialogSchliessen(); }}
        onClick={(e) => { if (e.target === dialog.current) dialogSchliessen(); }}
      >
        {dialogOffen && panel("dialog")}
      </dialog>
    </>
  );
}
