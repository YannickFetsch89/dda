// Seitenrahmen: Header, Kategorie-Leiste, Footer
import Link from "next/link";
import { KopfNav, LeisteVerhalten, ThemeToggle } from "./client";
import { Icon } from "./karten";
import { KATEGORIEN, katStil } from "@/lib/kategorien";
import { eventPoolLaden } from "@/lib/daten";
import { filtern, istKostenlos, kategorieZaehlen, stadtteileZaehlen } from "@/lib/ableitungen";
import { ZEITRAUM_OPTIONEN, plusTage } from "@/lib/datum";
import { stadtteilName } from "@/lib/stadtteile";
import { stadtteilPfad } from "@/lib/landing";
import { MAGAZIN_VERLINKT, SPIELPLAETZE_VERLINKT, WEIHNACHTSMAERKTE_VERLINKT } from "@/lib/schalter";
import { kontenAktiv } from "@/lib/konto/konfig";
import { LEISTEN_GUIDES } from "@/lib/guide-hubs";
import { guideZahlenLaden } from "@/lib/guide-zahlen";

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
        {/* Suchfeld nur auf breiten Bildschirmen (ab 1600 px); darunter die Lupe rechts (Auftraggeber 25.11.2026).
            Den Zeitraum wählt man über „Heute“, „Wochenende“ und den Kalender auf „Entdecken“. */}
        <form className="kopf__suche" action="/entdecken" role="search">
          <Icon name="search" />
          <label className="sr-only" htmlFor="kopf-suche">
            Suche
          </label>
          <input id="kopf-suche" name="q" type="search" placeholder="Events, Orte, Künstler …" />
        </form>
        <KopfNav />
        <div className="kopf__aktionen">
          <Link href="/entdecken#suche" className="icon-btn nur-mobil" aria-label="Suche">
            <Icon name="search" />
          </Link>
          {/* 1200–1599 px: Lupe klappt ein breites Suchfeld unter dem Kopf auf */}
          <details className="kopf__suchklappe">
            <summary className="icon-btn" aria-label="Suche">
              <Icon name="search" />
            </summary>
            <div className="kopf__suchpanel">
              <form className="container kopf__suchpanel-form" action="/entdecken" role="search">
                <Icon name="search" />
                <label className="sr-only" htmlFor="kopf-suche-klappe">
                  Suche
                </label>
                <input id="kopf-suche-klappe" name="q" type="search" placeholder="Events, Orte, Künstler …" />
                <button type="submit" className="btn btn--navy">Suchen</button>
              </form>
            </div>
          </details>
          <span className="nur-desktop">
            <ThemeToggle />
          </span>
          <Link href="/merkliste" className="icon-btn nur-desktop" aria-label="Merkliste">
            <Icon name="favorite" />
          </Link>
          {/* Immer „Mein Konto“: Der Kopf ist statisch, ein wechselnder Text würde nach dem Laden flackern (Plan 7.3).
              Mobil und am Desktop sichtbar, mobil rechts neben der Suche (17.11.2026). */}
          {/* Mobil das Personen-Symbol, am Desktop der Hauptbutton „mein.düsseldorf“ (Auftraggeber 25.11.2026).
              „Event melden“ steht dafür im Footer und im Mobilmenü. */}
          {kontenAktiv() && (
            <>
              <Link href="/konto" className="icon-btn nur-mobil" aria-label="Mein Konto" title="Mein Konto">
                <Icon name="person" />
              </Link>
              <Link href="/konto" className="btn btn--gold kopf__konto nur-desktop" title="Mein Konto">
                <Icon name="person" />
                mein.düsseldorf
              </Link>
            </>
          )}
          <details className="menue nur-mobil">
            <summary className="icon-btn" aria-label="Menü">
              <Icon name="menu" />
            </summary>
            <div className="popover">
              <span className="popover__titel popover__titel--erste">Events</span>
              <Link href="/entdecken">Entdecken</Link>
              <Link href="/heute">Heute</Link>
              <Link href="/wochenende">Wochenende</Link>
              <Link href="/ausblick">Ausblick</Link>
              <Link href="/kostenlos">Kostenlos</Link>
              <Link href="/orte">Veranstaltungsorte</Link>
              <Link href="/stadtteile">Stadtteile &amp; Karte</Link>
              {MAGAZIN_VERLINKT && <span className="popover__titel">Magazin</span>}
              {MAGAZIN_VERLINKT && <Link href="/magazin">Alle Beiträge</Link>}
              <span className="popover__titel">Guides</span>
              <Link href="/guides">Alle Guides</Link>
              {WEIHNACHTSMAERKTE_VERLINKT && <Link href="/guides/weihnachtsmaerkte">Weihnachtsmärkte</Link>}
              <Link href="/guides/restaurants-cafes">Restaurants &amp; Cafés</Link>
              <Link href="/guides/kneipen-bars">Kneipen &amp; Bars</Link>
              <Link href="/guides/clubs">Clubs</Link>
              {SPIELPLAETZE_VERLINKT && <Link href="/guides/spielplaetze">Spielplätze</Link>}
              {/* Trennstrich unter den Guides: kommt mit der Zwischenüberschrift (border-top wie bei „Guides“) */}
              <span className="popover__titel">Service</span>
              {kontenAktiv() && <Link href="/konto">Mein Konto</Link>}
              <Link href="/merkliste">Merkliste</Link>
              <Link href="/event-melden">Event melden</Link>
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
  const guideZahlen = await guideZahlenLaden();
  // Leiste nach Mockup-Variante 3 (Auftraggeber 27.11.2026, docs/mockups/leiste-events-guides.html): unter 1200 px
  // senkrecht „EVENTS“ und „GUIDES“; beim Runterscrollen klappt sie auf die zwei goldenen Wörter ein
  // (LeisteVerhalten in client.tsx). Am Desktop bleibt die Chip-Reihe der Kategorien wie bisher.
  return (
    <nav className="katleiste" id="katleiste" aria-label="Kategorien und Guides">
      <div className="katleiste__kompakt nur-mobil">
        <button type="button" className="katleiste__wort" data-ziel="events" aria-expanded="false" aria-controls="katleiste-klappe">
          Events<Icon name="expand_more" />
        </button>
        <span className="katleiste__punkt" aria-hidden />
        <button type="button" className="katleiste__wort" data-ziel="guides" aria-expanded="false" aria-controls="katleiste-klappe">
          Guides<Icon name="expand_more" />
        </button>
      </div>
      <div className="katleiste__klappe" id="katleiste-klappe">
      <div className="katleiste__innen">
      <div className="katleiste__inner">
        <span className="katleiste__senkrecht nur-mobil" aria-hidden><span>Events</span></span>
        {KATEGORIEN.map((k) => (
          <Link key={k.slug} href={`/kategorie/${k.slug}`} className="katitem" style={katStil(k.slug)}>
            <span className="katitem__kreis">
              <Icon name={k.icon} />
            </span>
            <span className="katitem__name">{k.name}</span>
            <span className="katitem__anzahl">{zaehler[k.slug]}</span>
          </Link>
        ))}
        <Link href="/kostenlos" className="katitem katitem--gratis">
          <span className="katitem__kreis">
            <Icon name="savings" />
          </span>
          <span className="katitem__name">Kostenlos</span>
          <span className="katitem__anzahl">{gratis}</span>
        </Link>
        {/* Guides in derselben Leiste, abgesetzt durch Trennstrich, senkrechtes „GUIDES“ und goldenen Rand;
            nur unter 1200 px – am Desktop steht das Menü „Guides ▾“ im Kopf */}
        <span className="katleiste__trenner nur-mobil" aria-hidden />
        <span className="katleiste__senkrecht nur-mobil" data-anker="guides" aria-hidden><span>Guides</span></span>
        {LEISTEN_GUIDES.map((g) => (
          <Link key={g.zahl} href={g.href} className="katitem katitem--guide nur-mobil">
            <span className="katitem__kreis">
              <Icon name={g.icon} />
            </span>
            <span className="katitem__name">{g.name}</span>
            <span className="katitem__anzahl">{guideZahlen[g.zahl] ?? ""}</span>
          </Link>
        ))}
      </div>
      </div>
      </div>
      <LeisteVerhalten />
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
          <p>
            Alle Events in Düsseldorf, jeden Tag neu gesammelt: Konzerte, Theater, Comedy, Partys und Familienprogramm.
            Dazu unsere Guides mit den besten Restaurants, Cafés, Kneipen, Bars und Clubs der Stadt
            {SPIELPLAETZE_VERLINKT ? " und allen öffentlichen Spielplätzen" : ""} – nach Stadtteil sortiert.{WEIHNACHTSMAERKTE_VERLINKT ? " Im Advent zeigt unser Weihnachtsmarkt-Guide, welcher Markt heute geöffnet hat." : ""} So seht ihr auf einen Blick, was ihr heute, morgen oder am Wochenende unternehmen könnt.
          </p>
          <Link href="/ueber" className="fuss__mehr">Mehr über uns</Link>
        </div>
        <div className="fuss__spalte">
          <b>Kategorien</b>
          {KATEGORIEN.slice(0, 6).map((k) => (
            <Link key={k.slug} href={`/kategorie/${k.slug}`}>
              {k.name}
            </Link>
          ))}
          <Link href="/entdecken">Alle Events</Link>
        </div>
        <div className="fuss__spalte">
          <b>Stadtteile</b>
          {top.filter((s) => stadtteilPfad(s.name)).map((s) => (
            <Link key={s.name} href={stadtteilPfad(s.name)!}>
              {stadtteilName(s.name)}
            </Link>
          ))}
          <Link href="/stadtteile">Alle Stadtteile</Link>
        </div>
        <div className="fuss__spalte">
          <b>Guides</b>
          {WEIHNACHTSMAERKTE_VERLINKT && <Link href="/guides/weihnachtsmaerkte">Weihnachtsmärkte</Link>}
          <Link href="/guides/restaurants-cafes">Restaurants & Cafés</Link>
          <Link href="/guides/kneipen-bars">Kneipen & Bars</Link>
          <Link href="/guides/clubs">Clubs</Link>
          {SPIELPLAETZE_VERLINKT && <Link href="/guides/spielplaetze">Spielplätze</Link>}
          <Link href="/orte">Veranstaltungsorte</Link>
          <Link href="/guides">Alle Guides</Link>
        </div>
        {MAGAZIN_VERLINKT && (
          <div className="fuss__spalte">
            <b>Magazin</b>
            <Link href="/magazin">Alle Beiträge</Link>
            <Link href="/magazin/redaktion">Unsere Redaktion</Link>
            <Link href="/rss">RSS-Feed</Link>
          </div>
        )}
        <div className="fuss__spalte">
          <b>Service</b>
          <Link href="/event-melden">Event melden</Link>
          <a href={`mailto:${KONTAKT_MAIL}?subject=Veranstalter`}>Für Veranstalter</a>
          <Link href="/#newsletter">Newsletter</Link>
          <Link href="/merkliste">Merkliste</Link>
          {kontenAktiv() && <Link href="/konto">Mein Konto</Link>}
        </div>
      </div>
      {/* Rechtliches mittig ganz unten, mit schmaler Trennlinie darüber */}
      <div className="container">
        <div className="fuss__unten">
          <Link href="/impressum">Impressum</Link>
          <Link href="/datenschutz">Datenschutz</Link>
          {kontenAktiv() && <Link href="/nutzungsbedingungen">Nutzungsbedingungen</Link>}
        </div>
      </div>
    </footer>
  );
}
