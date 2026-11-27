"use client";
// Kleine interaktive Bausteine (Client Components)
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Fragment, Suspense, useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { MAGAZIN_VERLINKT, SPIELPLAETZE_VERLINKT, WEIHNACHTSMAERKTE_VERLINKT } from "@/lib/schalter";
import {
  KONTO_EVENT, angemeldetOhneAlter, kontomodus, merkAbonnieren, merkenUmschalten, merkSnapshot, SCHLUESSEL, type KontoZustand,
} from "@/lib/konto/merk-store";

// ---------- Merkliste (Gerät in localStorage, mit Konto zusätzlich auf dem Server: lib/konto/merk-store.ts) ----------

const LEER: string[] = [];

/** Gemerkte IDs. Server-Snapshot ist immer leer: gecachte Seiten enthalten keinen Merkzustand (Plan 1.1). */
export function useMerkliste(): string[] {
  return useSyncExternalStore(merkAbonnieren, merkSnapshot, () => LEER);
}

/** Hinweis nach dem ersten Herz-Klick (Plan 7.2): nur abgemeldet, nur mit Konten-Schalter, nur einmal je Gerät. */
export const ERSTES_MERKEN_EVENT = "ddd-erstes-merken";
function erstesMerkenMelden() {
  if (document.body.dataset.konten !== "1" || kontomodus() || angemeldetOhneAlter()) return;
  try {
    if (window.localStorage.getItem(SCHLUESSEL.hinweis)) return;
    window.localStorage.setItem(SCHLUESSEL.hinweis, "1");
  } catch {
    return;
  }
  window.dispatchEvent(new Event(ERSTES_MERKEN_EVENT));
}

export function HerzButton({ id, titel, gross = false }: { id: string; titel: string; gross?: boolean }) {
  const gemerkt = useMerkliste().includes(id);
  return (
    <button
      type="button"
      className={gross ? "herz herz--gross" : "herz"}
      aria-pressed={gemerkt}
      aria-label={gemerkt ? `${titel} von der Merkliste entfernen` : `${titel} merken`}
      onClick={(ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        if (merkenUmschalten(id)) erstesMerkenMelden();
      }}
    >
      <span className="icon" aria-hidden data-icon="favorite" />
    </button>
  );
}

// ---------- Bild mit Fallback: eigenes Bild → Symbolbild → Kategorie-Platzhalter ----------

export function BildImg({
  src,
  ersatz = null,
  alt,
  icon,
  eager = false,
  vollstaendig = false,
  fokus,
  // Mit Alt-Text (Hero) „Symbolbild“; in Listen (alt="") auch beim Symbolbild leer – der Titel steht im Link
  symbolAlt = alt ? "Symbolbild" : "",
}: {
  src: string | null;
  ersatz?: string | null;
  alt: string;
  icon: string;
  eager?: boolean;
  /** Bild nicht beschneiden, sondern ganz zeigen und den Rand mit einer unscharfen Kopie füllen */
  vollstaendig?: boolean;
  /** Welcher Teil beim Beschneiden sichtbar bleibt (CSS object-position, z. B. "center bottom") */
  fokus?: string;
  /** Alt-Text, wenn statt des eigenen Bildes das Symbolbild erscheint (Standard: „Symbolbild“, in Listen leer) */
  symbolAlt?: string;
}) {
  // Kandidaten der Reihe nach; schlägt ein Bild fehl, kommt das nächste
  const kandidaten = [src, ersatz].filter((s): s is string => !!s);
  const [fehler, setFehler] = useState(0);
  const aktuell = kandidaten[fehler];
  const bildRef = useRef<HTMLImageElement>(null);
  // Schlägt das Bild schon vor der Hydrierung fehl (Server-HTML lädt sofort), kommt onError nie an – dann hing ein
  // kaputtes Bild statt des Symbolbilds auf der Seite (zakk, 19.11.2026). Nach dem Einhängen deshalb einmal nachsehen.
  useEffect(() => {
    const img = bildRef.current;
    if (img && img.complete && img.naturalWidth === 0) setFehler((n) => n + 1);
  }, [aktuell]);
  if (!aktuell) {
    return (
      <span className="bild__platzhalter" aria-hidden>
        <span className="icon" aria-hidden data-icon={icon} />
      </span>
    );
  }
  const istSymbol = aktuell === ersatz;
  return (
    <>
      {/* Externe Bilder aus vielen Quellen, daher kein next/image */}
      {vollstaendig && (
        // eslint-disable-next-line @next/next/no-img-element
        <img key={`${aktuell}-hg`} className="bild__unscharf" src={aktuell} alt="" aria-hidden referrerPolicy="no-referrer" />
      )}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        key={aktuell}
        ref={bildRef}
        className={vollstaendig ? "bild__ganz" : undefined}
        style={fokus && !istSymbol ? { objectPosition: fokus } : undefined}
        src={aktuell}
        alt={istSymbol ? symbolAlt : alt}
        loading={eager ? "eager" : "lazy"}
        decoding="async"
        referrerPolicy="no-referrer"
        onError={() => setFehler((n) => n + 1)}
      />
      {istSymbol && <span className="bild__symbol">Symbolbild</span>}
    </>
  );
}

// ---------- Google-Karte mit Zwei-Klick-Lösung (DSGVO) ----------
// Google Maps wird erst nach Klick geladen, vorher gehen keine Daten an Google.
// Die Zustimmung gilt danach für alle Karten (localStorage).

const KARTE_KEY = "ddd-karte-zustimmung";
const KARTE_EVENT = "ddd-karte-geaendert";

function karteAbonnieren(neu: () => void) {
  window.addEventListener(KARTE_EVENT, neu);
  window.addEventListener("storage", neu);
  return () => {
    window.removeEventListener(KARTE_EVENT, neu);
    window.removeEventListener("storage", neu);
  };
}

function karteZustimmung(): boolean {
  try {
    return window.localStorage.getItem(KARTE_KEY) === "ja";
  } catch {
    return false;
  }
}

export function GoogleKarte({ adresse, routeUrl }: { adresse: string; routeUrl: string }) {
  const zugestimmt = useSyncExternalStore(karteAbonnieren, karteZustimmung, () => false);
  const [nurEinmal, setNurEinmal] = useState(false);
  const anzeigen = zugestimmt || nurEinmal;

  const zustimmen = (merken: boolean) => {
    if (!merken) return setNurEinmal(true);
    try {
      window.localStorage.setItem(KARTE_KEY, "ja");
    } catch {
      setNurEinmal(true);
    }
    window.dispatchEvent(new Event(KARTE_EVENT));
  };

  return (
    <div className="karte-ausschnitt">
      {anzeigen ? (
        <iframe
          className="karte-ausschnitt__frame"
          src={`https://www.google.com/maps?q=${encodeURIComponent(adresse)}&output=embed&hl=de`}
          title={`Karte: ${adresse}`}
          loading="lazy"
          referrerPolicy="no-referrer"
          allowFullScreen
        />
      ) : (
        <div className="karte-ausschnitt__zustimmung">
          <span className="karte-ausschnitt__pin">
            <span className="icon" aria-hidden data-icon="location_on" />
          </span>
          <p>Beim Laden der Karte werden Daten (u.a. deine IP-Adresse) an Google übertragen.</p>
          <div>
            <button type="button" className="btn btn--gold" onClick={() => zustimmen(true)}>
              Karte anzeigen
            </button>
            <button type="button" className="link" onClick={() => zustimmen(false)}>
              Nur dieses Mal
            </button>
          </div>
        </div>
      )}
      <a className="karte-ausschnitt__route" href={routeUrl} target="_blank" rel="noopener noreferrer" aria-label={`Route zu ${adresse} in Google Maps`}>
        <span className="icon" aria-hidden data-icon="directions" />
        Route
      </a>
    </div>
  );
}

// ---------- Claim-Animation ----------

const WOERTER = ["heute", "heute Abend", "am Rhein", "am Wochenende"];

export function ClaimWort() {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(() => setI((x) => (x + 1) % WOERTER.length), 2400);
    return () => clearInterval(t);
  }, []);
  return (
    <span key={WOERTER[i]} className="claim-wort" aria-live="off">
      {WOERTER[i]}
    </span>
  );
}

// ---------- Horizontale Reihe mit Pfeilen ----------

export function Reihe({ children, breite, raster5 = false, label }: { children: ReactNode; breite: number; raster5?: boolean; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [rand, setRand] = useState({ links: false, rechts: false });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const pruefen = () => setRand({ links: el.scrollLeft > 4, rechts: el.scrollLeft + el.clientWidth < el.scrollWidth - 4 });
    pruefen();
    el.addEventListener("scroll", pruefen, { passive: true });
    window.addEventListener("resize", pruefen);
    return () => {
      el.removeEventListener("scroll", pruefen);
      window.removeEventListener("resize", pruefen);
    };
  }, []);

  const scrollen = (richtung: number) => ref.current?.scrollBy({ left: richtung * ref.current.clientWidth * 0.8, behavior: "smooth" });

  return (
    <div className="reihe-wrap">
      <div ref={ref} className={raster5 ? "reihe reihe--raster5" : "reihe"} style={{ ["--breite" as string]: `${breite}px` }} role="list" aria-label={label}>
        {children}
      </div>
      <button type="button" className="reihe__pfeil reihe__pfeil--l" disabled={!rand.links} onClick={() => scrollen(-1)} aria-label="Zurück scrollen">
        <span className="icon" aria-hidden data-icon="arrow_back" />
      </button>
      <button type="button" className="reihe__pfeil reihe__pfeil--r" disabled={!rand.rechts} onClick={() => scrollen(1)} aria-label="Weiter scrollen">
        <span className="icon" aria-hidden data-icon="arrow_forward" />
      </button>
    </div>
  );
}

// ---------- Theme ----------

export function ThemeToggle() {
  return (
    <button
      type="button"
      className="icon-btn"
      aria-label="Hell/Dunkel umschalten"
      onClick={() => {
        const root = document.documentElement;
        const neu = root.dataset.theme === "dark" ? "light" : "dark";
        root.dataset.theme = neu;
        try {
          window.localStorage.setItem("ddd-theme", neu);
        } catch {
          // ignorieren
        }
      }}
    >
      <span className="icon" aria-hidden data-icon="dark_mode" />
    </button>
  );
}

// ---------- Navigation mit aktivem Zustand ----------

// Events und Guides gleichwertig (Auftraggeber 27.11.2026): „Heute“, „Wochenende“ und „Ausblick“ stehen als
// Umschalter oben auf den Event-Seiten (EventsUmschalter), „Für dich“ auf der Startseite und im Profil.
// Gast und Konto haben dieselben fünf Tabs; „Profil“ führt Gäste zur Anmeldung.
const TABS = [
  { href: "/", icon: "home", label: "Start" },
  { href: "/entdecken", icon: "event", label: "Events" },
  { href: "/guides", icon: "explore", label: "Guides" },
  { href: "/merkliste", icon: "favorite", label: "Merkliste" },
  { href: "/konto", icon: "person", label: "Profil" },
];
const TABS_KONTO = TABS;

/** Alle Seiten, die zur Welt „Events“ gehören (Listen, Tage, Kategorien, Event-Seiten, Stadtteile) */
const EVENT_PRAEFIXE = ["/entdecken", "/heute", "/morgen", "/tag", "/wochenende", "/ausblick", "/kostenlos", "/kategorie", "/event", "/reihe", "/stadtteil", "/stadtteile", "/orte"];
/** Alle Seiten, die zur Welt „Guides“ gehören (Hubs und Guide-Detailseiten) */
const GUIDE_PRAEFIXE = ["/guides"];

/** Pfad ist genau ein Präfix oder liegt darunter („/tag/2026-11-27“), aber nicht „/tagung“ */
function beginntMit(pfad: string, praefixe: string[]) {
  return praefixe.some((p) => pfad === p || pfad.startsWith(`${p}/`));
}

export function istEventSeite(pfad: string | null) {
  return pfad !== null && beginntMit(pfad, EVENT_PRAEFIXE);
}
export function istGuideSeite(pfad: string | null) {
  return pfad !== null && beginntMit(pfad, GUIDE_PRAEFIXE);
}

function istAktiv(pfad: string | null, href: string) {
  if (pfad === null) return false;
  if (href === "/") return pfad === "/";
  if (href === "/entdecken") return istEventSeite(pfad);
  if (href === "/guides") return istGuideSeite(pfad);
  if (href === "/heute") return pfad === "/heute" || pfad.startsWith("/tag/");
  return pfad.startsWith(href);
}

// Profil-Tab: Übersicht und Unterseiten von Mein dies.das samt „Für dich“; für Gäste auch Anmelden & Co.
const PROFIL_PFADE = new Set(["/konto", "/konto/einstellungen", "/konto/datenschutz", "/konto/interessen", "/konto/erlebt", "/konto/willkommen", "/konto/fuer-dich"]);
export function istAktivKonto(pfad: string | null, href: string) {
  if (pfad === null) return false;
  if (href === "/konto") return PROFIL_PFADE.has(pfad);
  if (href === "/merkliste") return pfad === href;
  return istAktiv(pfad, href);
}
function istAktivGast(pfad: string | null, href: string) {
  if (pfad === null) return false;
  if (href === "/konto") return pfad === "/konto" || pfad.startsWith("/konto/");
  return istAktiv(pfad, href);
}

const zustandAbo = (cb: () => void) => {
  window.addEventListener(KONTO_EVENT, cb);
  return () => window.removeEventListener(KONTO_EVENT, cb);
};
const htmlZustand = (): KontoZustand => {
  const w = document.documentElement.dataset.konto;
  return w === "1" || w === "0" ? w : null;
};
/**
 * Kontozustand für die Oberfläche (Plan Mein Bereich 3.0): „1“, „0“ oder null. Liest html[data-konto], das
 * kontoAttributAbgleichen (lib/konto/merk-store.ts) pflegt. Auf dem Server und vor der Hydration immer abgemeldet.
 */
export function useKontoZustand(): KontoZustand {
  return useSyncExternalStore(zustandAbo, htmlZustand, () => null);
}

const nieAbo = () => () => {};
/**
 * false auf dem Server und während der Hydration, danach true. Für `hidden` an TabBar und Seitenleiste: Das Attribut
 * darf nicht im Server-HTML stehen (dort ist der Zustand immer „abgemeldet“), sonst könnte es vor der Hydration die
 * angemeldete Leiste verdecken, die CSS über html[data-konto] schon zeigt (Cursor-Befund 2, Plan 3.9).
 */
export function useHydriert(): boolean {
  return useSyncExternalStore(nieAbo, () => true, () => false);
}

function TabBarMitPfad() {
  return <TabBarListen pfad={usePathname()} />;
}

// Ohne Suspense würde usePathname das Prerendering blockieren; Fallback zeigt die Leiste ohne Aktiv-Zustand
export function TabBar() {
  return (
    <Suspense fallback={<TabBarListen pfad={null} />}>
      <TabBarMitPfad />
    </Suspense>
  );
}

/**
 * Beide Leisten stehen im HTML (Plan Mein Bereich 3.9). Sichtbar ist genau eine: CSS über html[data-konto] mit
 * display:none, schon vor der Hydration. Erst danach setzt die Komponente zusätzlich `hidden` an der inaktiven Leiste.
 */
function TabBarListen({ pfad }: { pfad: string | null }) {
  const konto = useKontoZustand() === "1";
  const hydriert = useHydriert();
  return (
    <>
      <nav className="tabbar tabbar--gast" aria-label="Hauptnavigation" hidden={hydriert && konto}>
        {TABS.map((t) => (
          <Link key={t.href} href={t.href} aria-current={istAktivGast(pfad, t.href) ? "page" : undefined}>
            <span className="icon" aria-hidden data-icon={t.icon} />
            {t.label}
          </Link>
        ))}
      </nav>
      <nav className="tabbar tabbar--konto" aria-label="Hauptnavigation" hidden={hydriert && !konto}>
        {TABS_KONTO.map((t) => (
          <Link key={t.href} href={t.href} aria-current={istAktivKonto(pfad, t.href) ? "page" : undefined}>
            <span className="icon" aria-hidden data-icon={t.icon} />
            {t.label}
          </Link>
        ))}
      </nav>
    </>
  );
}

// Kopf am Desktop (Auftraggeber 27.11.2026): „Events ▾“ und „Guides ▾“ als gleich gebaute Aufklappmenüs,
// daneben das Magazin. Veranstaltungsorte und „Stadtteile & Karte“ zeigen bisher nur Events und stehen deshalb
// unter einem Trennstrich am Ende des Events-Menüs (später mit den Guide-Orten nach Stadtteilen verschmelzen).
const NAV = [
  // Magazin (Plan Redaktion 5.9, E10)
  ...(MAGAZIN_VERLINKT ? [{ href: "/magazin", label: "Magazin" }] : []),
];

type MenueLink = { href: string; label: string; icon: string; trenner?: boolean };

export const EVENT_LINKS: MenueLink[] = [
  { href: "/entdecken", label: "Alle Events", icon: "event" },
  { href: "/heute", label: "Heute", icon: "today" },
  { href: "/wochenende", label: "Wochenende", icon: "weekend" },
  { href: "/ausblick", label: "Ausblick", icon: "date_range" },
  { href: "/kostenlos", label: "Kostenlos", icon: "savings" },
  { href: "/orte", label: "Veranstaltungsorte", icon: "location_city", trenner: true },
  { href: "/stadtteile", label: "Stadtteile & Karte", icon: "map" },
];

export const GUIDE_LINKS: MenueLink[] = [
  { href: "/guides", label: "Alle Guides", icon: "explore" },
  // Saison-Guide zuerst, solange der Schalter an ist (Plan Weihnachtsmärkte 5.6)
  ...(WEIHNACHTSMAERKTE_VERLINKT ? [{ href: "/guides/weihnachtsmaerkte", label: "Weihnachtsmärkte", icon: "wm:markt" }] : []),
  { href: "/guides/restaurants-cafes", label: "Restaurants & Cafés", icon: "restaurant" },
  { href: "/guides/kneipen-bars", label: "Kneipen & Bars", icon: "sports_bar" },
  { href: "/guides/clubs", label: "Clubs", icon: "nightlife" },
  ...(SPIELPLAETZE_VERLINKT ? [{ href: "/guides/spielplaetze", label: "Spielplätze", icon: "sp:spielplatz" }] : []),
];

/** Aufklappmenü im Kopf (Events, Guides): gleiche Form, damit beide Welten gleich viel Gewicht haben */
function KopfMenue({ titel, aktiv, links, pfad, links_buendig = false }: {
  titel: string; aktiv: boolean; links: MenueLink[]; pfad: string | null; links_buendig?: boolean;
}) {
  return (
    <details className={links_buendig ? "kopf__guides kopf__guides--links" : "kopf__guides"}>
      <summary className={aktiv ? "is-aktiv" : ""}>
        {titel}<span className="icon" aria-hidden data-icon="expand_more" />
      </summary>
      <div className="kopf__guides-menue">
        {links.map((g) => (
          <Fragment key={g.href}>
            {g.trenner && <span className="kopf__menue-trenner" aria-hidden />}
            <Link href={g.href} aria-current={pfad === g.href ? "page" : undefined}>
              <span className="icon" aria-hidden data-icon={g.icon} />{g.label}
            </Link>
          </Fragment>
        ))}
      </div>
    </details>
  );
}

function KopfNavMitPfad() {
  return <KopfNavListe pfad={usePathname()} />;
}

export function KopfNav() {
  return (
    <Suspense fallback={<KopfNavListe pfad={null} />}>
      <KopfNavMitPfad />
    </Suspense>
  );
}

function KopfNavListe({ pfad }: { pfad: string | null }) {
  return (
    <nav className="kopf__nav" aria-label="Bereiche">
      <KopfMenue titel="Events" aktiv={istEventSeite(pfad)} links={EVENT_LINKS} pfad={pfad} links_buendig />
      <KopfMenue titel="Guides" aktiv={istGuideSeite(pfad)} links={GUIDE_LINKS} pfad={pfad} />
      {NAV.map((n) => (
        <Link key={n.href} href={n.href} aria-current={istAktiv(pfad, n.href) ? "page" : undefined}>
          {n.label}
        </Link>
      ))}
    </nav>
  );
}

// ---------- Leiste unter dem Kopf: einklappen beim Scrollen (Mockup-Variante 3, Auftraggeber 27.11.2026) ----------

/**
 * Unter 1200 px klappt die Leiste (rahmen.tsx, #katleiste) beim Runterscrollen auf die goldenen Wörter
 * „EVENTS · GUIDES“ ein. „Events“ klappt sie am Anfang auf, „Guides“ klappt sie auf und schiebt sie zu den Guides.
 * Ein zweiter Tipp oder weiteres Scrollen klappt sie wieder ein; ganz oben ist sie immer offen.
 * Nur wenn die Leiste klebt (nicht auf den Guide-Seiten, dort hat sie position: relative) – sonst würde das
 * Einklappen außerhalb des Blickfelds nur den Inhalt verschieben.
 */
export function LeisteVerhalten() {
  useEffect(() => {
    const nav = document.getElementById("katleiste");
    const reihe = nav?.querySelector<HTMLElement>(".katleiste__inner");
    const anker = nav?.querySelector<HTMLElement>('[data-anker="guides"]');
    if (!nav || !reihe || !anker) return;
    const schmal = window.matchMedia("(max-width: 1199px)");
    const knopf = (z: string) => nav.querySelector<HTMLButtonElement>(`.katleiste__wort[data-ziel="${z}"]`);
    let zu = false; // weit genug gescrollt: nur die zwei Wörter
    let offen = false; // eingeklappt, aber per Tipp aufgeklappt
    let offenBeiY = 0; // Scrollstand beim Aufklappen

    const aktiv = () => schmal.matches && getComputedStyle(nav).position === "sticky";
    const guidesStart = () => Math.max(0, anker.getBoundingClientRect().left - reihe.getBoundingClientRect().left + reihe.scrollLeft - 12);
    const zeichnen = () => {
      nav.classList.toggle("is-zu", zu);
      nav.classList.toggle("is-offen", zu && offen);
      const imGuides = reihe.scrollLeft >= guidesStart() - 40;
      for (const z of ["events", "guides"]) {
        const b = knopf(z);
        if (!b) continue;
        b.setAttribute("aria-expanded", String(!zu || offen));
        b.classList.toggle("is-im-blick", zu && offen && (z === "guides") === imGuides);
      }
    };
    const scrollen = () => {
      if (!aktiv()) {
        if (zu) { zu = offen = false; zeichnen(); }
        return;
      }
      const y = window.scrollY;
      if (!zu && y > 140) { zu = true; offen = false; zeichnen(); }
      else if (zu && y < 20) { zu = offen = false; zeichnen(); }
      else if (zu && offen && Math.abs(y - offenBeiY) > 120) { offen = false; zeichnen(); }
    };
    const tippen = (z: string) => () => {
      const ziel = z === "guides" ? guidesStart() : 0;
      const schonDa = Math.abs(reihe.scrollLeft - ziel) < 30;
      if (offen && schonDa) { offen = false; zeichnen(); return; } // zweiter Tipp: wieder einklappen
      const warZu = !offen;
      offen = true;
      offenBeiY = window.scrollY;
      zeichnen();
      reihe.scrollTo({ left: ziel, behavior: warZu ? "instant" : "smooth" });
    };
    const klicks = (["events", "guides"] as const).map((z) => [knopf(z), tippen(z)] as const);
    klicks.forEach(([b, f]) => b?.addEventListener("click", f));
    window.addEventListener("scroll", scrollen, { passive: true });
    reihe.addEventListener("scroll", zeichnen, { passive: true });
    schmal.addEventListener("change", scrollen);
    scrollen();
    return () => {
      klicks.forEach(([b, f]) => b?.removeEventListener("click", f));
      window.removeEventListener("scroll", scrollen);
      reihe.removeEventListener("scroll", zeichnen);
      schmal.removeEventListener("change", scrollen);
    };
  }, []);
  return null;
}

// ---------- Dropdowns (<details>) schließen nach Auswahl oder Klick daneben ----------

export function DetailsVerhalten() {
  useEffect(() => {
    const klick = (ev: MouseEvent) => {
      const ziel = ev.target as HTMLElement;
      document.querySelectorAll<HTMLDetailsElement>("details[open]").forEach((d) => {
        const innen = d.contains(ziel);
        const aufSummary = innen && !!ziel.closest("summary") && ziel.closest("details") === d;
        if (!innen || (!aufSummary && ziel.closest("a"))) d.open = false;
        // Klick auf den abgedunkelten Hintergrund (::before) trifft das details-Element selbst
        if (ziel === d) d.open = false;
      });
    };
    const taste = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") document.querySelectorAll<HTMLDetailsElement>("details[open]").forEach((d) => (d.open = false));
    };
    // Such-Klappe im Kopf (1200–1599 px): beim Aufklappen gleich ins Suchfeld springen
    const umschalten = (ev: Event) => {
      const d = ev.target as HTMLDetailsElement;
      if (d.open && d.classList?.contains("kopf__suchklappe")) d.querySelector<HTMLInputElement>("input[type=search]")?.focus();
    };
    document.addEventListener("click", klick);
    document.addEventListener("keydown", taste);
    document.addEventListener("toggle", umschalten, true); // toggle steigt nicht auf → Capture
    return () => {
      document.removeEventListener("click", klick);
      document.removeEventListener("keydown", taste);
      document.removeEventListener("toggle", umschalten, true);
    };
  }, []);
  return null;
}

// ---------- Newsletter (Anmeldung über /api/newsletter, Double-Opt-in: Bestätigungsmail vom Job, Plan Admin 4.9) ----------

export function NewsletterForm() {
  const [zustand, setZustand] = useState<"bereit" | "sendet" | "fertig">("bereit");
  const [fehler, setFehler] = useState<string | null>(null);
  if (zustand === "fertig") {
    return (
      <p style={{ fontWeight: 700 }} role="status">
        Fast geschafft! Wir schicken dir eine Mail mit einem Bestätigungslink. Erst wenn du ihn anklickst, bekommst du den Newsletter.
      </p>
    );
  }
  return (
    <div className="newsletter__form">
    <form
      onSubmit={async (ev) => {
        ev.preventDefault();
        const form = new FormData(ev.currentTarget);
        setZustand("sendet");
        setFehler(null);
        try {
          const r = await fetch("/api/newsletter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: form.get("email"), website: form.get("website") }),
          });
          const daten = (await r.json().catch(() => ({}))) as { fehler?: string };
          if (!r.ok) throw new Error(daten.fehler ?? "Das hat leider nicht geklappt.");
          setZustand("fertig");
        } catch (e) {
          setFehler(e instanceof Error ? e.message : "Das hat leider nicht geklappt.");
          setZustand("bereit");
        }
      }}
    >
      <label className="sr-only" htmlFor="newsletter-mail">
        E-Mail-Adresse
      </label>
      <input id="newsletter-mail" name="email" type="email" required maxLength={254} placeholder="deine@email.de" autoComplete="email" />
      {/* Honeypot gegen Bots – für Menschen unsichtbar */}
      <input type="text" name="website" tabIndex={-1} autoComplete="off" aria-hidden className="honigtopf" />
      <button type="submit" className="btn btn--navy" disabled={zustand === "sendet"}>
        {zustand === "sendet" ? "Wird gesendet…" : "Abonnieren"}
      </button>
    </form>
    {fehler && <p className="newsletter__fehler" role="alert">{fehler}</p>}
    {/* Hinweis vom Anwalt freigegeben 23.11.2026 (docs/anwalt-newsletter-doi-2026-11-23.md) */}
    <p className="newsletter__hinweis">
      Mit der Anmeldung bekommst du eine Mail mit Bestätigungslink. Erst danach schicken wir dir donnerstags unseren
      Newsletter. Abmelden kannst du dich jederzeit über den Link in jeder Mail. Mehr in der{" "}
      <Link href="/datenschutz#newsletter">Datenschutzerklärung</Link>.
    </p>
    </div>
  );
}

// ---------- Teilen ----------

export function TeilenLeiste({ titel, pfad }: { titel: string; pfad: string }) {
  const [kopiert, setKopiert] = useState(false);
  const url = () => new URL(pfad, window.location.origin).toString();
  return (
    <div className="teilen">
      <button
        type="button"
        onClick={() => window.open(`https://wa.me/?text=${encodeURIComponent(`${titel} ${url()}`)}`, "_blank", "noopener")}
      >
        <span className="icon" aria-hidden data-icon="chat" />WhatsApp
      </button>
      <button
        type="button"
        onClick={async () => {
          // Instagram hat keinen Web-Share-Link, daher Web Share API bzw. Link kopieren
          if (navigator.share) {
            try {
              await navigator.share({ title: titel, url: url() });
              return;
            } catch {
              // abgebrochen
            }
          }
          await navigator.clipboard?.writeText(url());
          setKopiert(true);
        }}
      >
        <span className="icon" aria-hidden data-icon="photo_camera" />Instagram
      </button>
      <button
        type="button"
        onClick={async () => {
          await navigator.clipboard?.writeText(url());
          setKopiert(true);
          setTimeout(() => setKopiert(false), 2000);
        }}
      >
        <span className="icon" aria-hidden data-icon="link" />
        {kopiert ? "Kopiert!" : "Link kopieren"}
      </button>
    </div>
  );
}

export function TeilenButton({ titel, pfad }: { titel: string; pfad: string }) {
  return (
    <button
      type="button"
      className="rund-weiss"
      aria-label="Teilen"
      onClick={async () => {
        const url = new URL(pfad, window.location.origin).toString();
        if (navigator.share) {
          try {
            await navigator.share({ title: titel, url });
          } catch {
            // abgebrochen
          }
        } else {
          await navigator.clipboard?.writeText(url);
        }
      }}
    >
      <span className="icon" aria-hidden data-icon="ios_share" />
    </button>
  );
}

export function ZurueckButton() {
  const router = useRouter();
  return (
    <button
      type="button"
      className="rund-weiss"
      aria-label="Zurück"
      onClick={() => (window.history.length > 1 ? router.back() : router.push("/"))}
    >
      <span className="icon" aria-hidden data-icon="arrow_back" />
    </button>
  );
}
