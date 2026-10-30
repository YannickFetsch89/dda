// Seitenrahmen: Header, Kategorie-Leiste, Footer
import Link from "next/link";
import { KopfNav, ThemeToggle } from "./client";
import { DatumPill } from "./datum-waehler";
import { Icon } from "./karten";
import { KATEGORIEN, katStil } from "@/lib/kategorien";
import { eventPoolLaden } from "@/lib/daten";
import { filtern, istKostenlos, kategorieZaehlen, stadtteileZaehlen } from "@/lib/ableitungen";
import { ZEITRAUM_OPTIONEN, plusTage } from "@/lib/datum";
import { stadtteilName } from "@/lib/stadtteile";

// Adresse für "Event melden" – vor dem Livegang prüfen
export const KONTAKT_MAIL = "hallo@diesdas.events";

export function Wortmarke({ gross = false }: { gross?: boolean }) {
  return (
    <Link href="/" className="wortmarke" style={gross ? { fontSize: 28 } : undefined} aria-label="dies.das.düsseldorf – Startseite">
      dies<span>.</span>das<span>.</span>düsseldorf
    </Link>
  );
}

export function Kopf() {
  return (
    <header className="kopf">
      <div className="container kopf__inner">
        <Wortmarke />
        <form className="kopf__suche" action="/entdecken" role="search">
          <Icon name="search" />
          <label className="sr-only" htmlFor="kopf-suche">
            Suche
          </label>
          <input id="kopf-suche" name="q" type="search" placeholder="Events, Orte, Künstler …" />
          <DatumPill />
        </form>
        <KopfNav />
        <div className="kopf__aktionen">
          <Link href="/entdecken#suche" className="icon-btn nur-mobil" aria-label="Suche">
            <Icon name="search" />
          </Link>
          <span className="nur-desktop">
            <ThemeToggle />
          </span>
          <Link href="/merkliste" className="icon-btn nur-desktop" aria-label="Merkliste">
            <Icon name="favorite" />
          </Link>
          <a href={`mailto:${KONTAKT_MAIL}?subject=Event%20melden`} className="btn btn--gold nur-desktop">
            Event melden
          </a>
          <details className="menue nur-mobil">
            <summary className="icon-btn" aria-label="Menü">
              <Icon name="menu" />
            </summary>
            <div className="popover">
              <Link href="/entdecken">Entdecken</Link>
              <Link href="/heute">Heute</Link>
              <Link href="/wochenende">Wochenende</Link>
              <Link href="/restaurants">Restaurants & Cafés</Link>
              <Link href="/stadtteile">Stadtteile &amp; Karte</Link>
              <Link href="/merkliste">Merkliste</Link>
              <a href={`mailto:${KONTAKT_MAIL}?subject=Event%20melden`}>Event melden</a>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 4px 4px 12px", fontSize: 14, fontWeight: 600 }}>
                Dunkler Modus <ThemeToggle />
              </div>
            </div>
          </details>
        </div>
      </div>
    </header>
  );
}

export async function KategorieLeiste() {
  const pool = await eventPoolLaden();
  // Zählwerte für die kommenden 7 Tage
  const woche = filtern(pool.events, { von: pool.heute, bis: plusTage(pool.heute, 6) });
  const zaehler = kategorieZaehlen(woche);
  const gratis = woche.filter(istKostenlos).length;
  return (
    <nav className="katleiste" aria-label="Kategorien">
      <div className="katleiste__inner">
        {KATEGORIEN.map((k) => (
          <Link key={k.slug} href={`/entdecken?kategorie=${k.slug}&datum=woche`} className="katitem" style={katStil(k.slug)}>
            <span className="katitem__kreis">
              <Icon name={k.icon} />
            </span>
            <span className="katitem__name">{k.name}</span>
            <span className="katitem__anzahl">{zaehler[k.slug]}</span>
          </Link>
        ))}
        <Link href="/entdecken?preis=kostenlos&datum=woche" className="katitem katitem--gratis">
          <span className="katitem__kreis">
            <Icon name="savings" />
          </span>
          <span className="katitem__name">Kostenlos</span>
          <span className="katitem__anzahl">{gratis}</span>
        </Link>
      </div>
    </nav>
  );
}

export async function DatenHinweis() {
  const pool = await eventPoolLaden();
  if (pool.quelle !== "beispiel") return null;
  return (
    <div className="daten-hinweis" role="status">
      <div className="container">
        <Icon name="info" />
        Vorschau mit Beispieldaten – die Supabase-Verbindung ist nicht konfiguriert oder nicht erreichbar.
      </div>
    </div>
  );
}

export async function Fuss() {
  const pool = await eventPoolLaden();
  const top = stadtteileZaehlen(pool.events).slice(0, 5);
  return (
    <footer className="fuss">
      <div className="container fuss__raster">
        <div className="fuss__marke">
          <Wortmarke gross />
          <p>Alle Events in Düsseldorf, jeden Tag neu gesammelt.</p>
        </div>
        <div className="fuss__spalte">
          <b>Kategorien</b>
          {KATEGORIEN.slice(0, 6).map((k) => (
            <Link key={k.slug} href={`/entdecken?kategorie=${k.slug}`}>
              {k.name}
            </Link>
          ))}
        </div>
        <div className="fuss__spalte">
          <b>Stadtteile</b>
          {top.map((s) => (
            <Link key={s.name} href={`/entdecken?stadtteil=${encodeURIComponent(s.name)}`}>
              {stadtteilName(s.name)}
            </Link>
          ))}
          <Link href="/stadtteile">Alle Stadtteile</Link>
        </div>
        <div className="fuss__spalte">
          <b>Guides</b>
          <Link href="/restaurants">Restaurants & Cafés</Link>
        </div>
        <div className="fuss__spalte">
          <b>Service</b>
          <a href={`mailto:${KONTAKT_MAIL}?subject=Event%20melden`}>Event melden</a>
          <a href={`mailto:${KONTAKT_MAIL}?subject=Veranstalter`}>Für Veranstalter</a>
          <Link href="/#newsletter">Newsletter</Link>
          <Link href="/merkliste">Merkliste</Link>
        </div>
        <div className="fuss__spalte">
          <b>DDD</b>
          <span>Über uns</span>
          <a href="https://www.instagram.com/dies.das.duesseldorf/" target="_blank" rel="noopener">Instagram</a>
          <Link href="/impressum">Impressum</Link>
          <Link href="/datenschutz">Datenschutz</Link>
        </div>
      </div>
    </footer>
  );
}
