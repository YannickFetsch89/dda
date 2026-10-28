"use client";
// Kleine interaktive Bausteine (Client Components)
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Suspense, useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";

// ---------- Merkliste (anonym in localStorage) ----------

const MERK_KEY = "ddd-merkliste";
const MERK_EVENT = "ddd-merkliste-geaendert";

function merklisteLesen(): string[] {
  try {
    const roh = window.localStorage.getItem(MERK_KEY);
    const liste = roh ? JSON.parse(roh) : [];
    return Array.isArray(liste) ? liste.filter((x) => typeof x === "string") : [];
  } catch {
    return [];
  }
}

let merkCache: { roh: string | null; liste: string[] } = { roh: null, liste: [] };

function merkSnapshot(): string[] {
  let roh: string | null = null;
  try {
    roh = window.localStorage.getItem(MERK_KEY);
  } catch {
    roh = null;
  }
  if (roh !== merkCache.roh) merkCache = { roh, liste: merklisteLesen() };
  return merkCache.liste;
}

const LEER: string[] = [];

function merkAbonnieren(callback: () => void) {
  window.addEventListener(MERK_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(MERK_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

export function useMerkliste(): string[] {
  return useSyncExternalStore(merkAbonnieren, merkSnapshot, () => LEER);
}

function merkenUmschalten(id: string) {
  const liste = merklisteLesen();
  const neu = liste.includes(id) ? liste.filter((x) => x !== id) : [...liste, id];
  try {
    window.localStorage.setItem(MERK_KEY, JSON.stringify(neu));
  } catch {
    // Speicher nicht verfügbar (privater Modus) – Merken bleibt dann wirkungslos
  }
  window.dispatchEvent(new Event(MERK_EVENT));
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
        merkenUmschalten(id);
      }}
    >
      <span className="icon" aria-hidden>
        favorite
      </span>
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
}: {
  src: string | null;
  ersatz?: string | null;
  alt: string;
  icon: string;
  eager?: boolean;
  /** Bild nicht beschneiden, sondern ganz zeigen und den Rand mit einer unscharfen Kopie füllen */
  vollstaendig?: boolean;
}) {
  // Kandidaten der Reihe nach; schlägt ein Bild fehl, kommt das nächste
  const kandidaten = [src, ersatz].filter((s): s is string => !!s);
  const [fehler, setFehler] = useState(0);
  const aktuell = kandidaten[fehler];
  if (!aktuell) {
    return (
      <span className="bild__platzhalter" aria-hidden>
        <span className="icon">{icon}</span>
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
        className={vollstaendig ? "bild__ganz" : undefined}
        src={aktuell}
        alt={istSymbol ? "Symbolbild" : alt}
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
          referrerPolicy="no-referrer-when-downgrade"
          allowFullScreen
        />
      ) : (
        <div className="karte-ausschnitt__zustimmung">
          <span className="karte-ausschnitt__pin">
            <span className="icon" aria-hidden>
              location_on
            </span>
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
        <span className="icon" aria-hidden>
          directions
        </span>
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
        <span className="icon">arrow_back</span>
      </button>
      <button type="button" className="reihe__pfeil reihe__pfeil--r" disabled={!rand.rechts} onClick={() => scrollen(1)} aria-label="Weiter scrollen">
        <span className="icon">arrow_forward</span>
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
      <span className="icon">dark_mode</span>
    </button>
  );
}

// ---------- Navigation mit aktivem Zustand ----------

const TABS = [
  { href: "/", icon: "home", label: "Start" },
  { href: "/entdecken", icon: "explore", label: "Entdecken" },
  { href: "/heute", icon: "today", label: "Heute" },
  { href: "/wochenende", icon: "weekend", label: "Wochenende" },
  { href: "/merkliste", icon: "favorite", label: "Merkliste" },
];

function istAktiv(pfad: string | null, href: string) {
  if (pfad === null) return false;
  if (href === "/") return pfad === "/";
  if (href === "/heute") return pfad === "/heute" || pfad.startsWith("/tag/");
  return pfad.startsWith(href);
}

function TabBarMitPfad() {
  return <TabBarListe pfad={usePathname()} />;
}

// Ohne Suspense würde usePathname das Prerendering blockieren; Fallback zeigt die Leiste ohne Aktiv-Zustand
export function TabBar() {
  return (
    <Suspense fallback={<TabBarListe pfad={null} />}>
      <TabBarMitPfad />
    </Suspense>
  );
}

function TabBarListe({ pfad }: { pfad: string | null }) {
  return (
    <nav className="tabbar" aria-label="Hauptnavigation">
      {TABS.map((t) => (
        <Link key={t.href} href={t.href} aria-current={istAktiv(pfad, t.href) ? "page" : undefined}>
          <span className="icon" aria-hidden>
            {t.icon}
          </span>
          {t.label}
        </Link>
      ))}
    </nav>
  );
}

const NAV = [
  { href: "/entdecken", label: "Entdecken" },
  { href: "/heute", label: "Heute" },
  { href: "/wochenende", label: "Wochenende" },
  { href: "/stadtteile", label: "Karte" },
];

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
      {NAV.map((n) => (
        <Link key={n.href} href={n.href} aria-current={istAktiv(pfad, n.href) ? "page" : undefined}>
          {n.label}
        </Link>
      ))}
    </nav>
  );
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
    document.addEventListener("click", klick);
    document.addEventListener("keydown", taste);
    return () => {
      document.removeEventListener("click", klick);
      document.removeEventListener("keydown", taste);
    };
  }, []);
  return null;
}

// ---------- Newsletter (noch ohne Backend) ----------

export function NewsletterForm() {
  const [gesendet, setGesendet] = useState(false);
  if (gesendet) return <p style={{ fontWeight: 700 }}>Danke! Der Newsletter startet in Kürze, wir melden uns.</p>;
  return (
    <form
      onSubmit={(ev) => {
        ev.preventDefault();
        setGesendet(true);
      }}
    >
      <label className="sr-only" htmlFor="newsletter-mail">
        E-Mail-Adresse
      </label>
      <input id="newsletter-mail" type="email" required placeholder="deine@email.de" autoComplete="email" />
      <button type="submit" className="btn btn--navy">
        Abonnieren
      </button>
    </form>
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
        <span className="icon">chat</span>WhatsApp
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
        <span className="icon">photo_camera</span>Instagram
      </button>
      <button
        type="button"
        onClick={async () => {
          await navigator.clipboard?.writeText(url());
          setKopiert(true);
          setTimeout(() => setKopiert(false), 2000);
        }}
      >
        <span className="icon">link</span>
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
      <span className="icon">ios_share</span>
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
      <span className="icon">arrow_back</span>
    </button>
  );
}
