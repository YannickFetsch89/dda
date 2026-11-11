// Tagesplaner (Design-Ansicht 04), genutzt von /heute und /tag/[datum]
import Link from "next/link";
import { Icon, Leer } from "./karten";
import { Zeitleiste, type Abschnitt } from "./zeitleiste";
import { eventPoolLaden } from "@/lib/daten";
import { TAGESZEITEN, ersteUhrzeitIn, filtern, nachZeit, tageszeiten } from "@/lib/ableitungen";
import { WT_LANG, plusTage, tagMonat, wochentag } from "@/lib/datum";
import { jsonLdText } from "@/lib/json-ld";
import { eventListeJsonLd } from "@/lib/listen-json-ld";
import { datumText, standText, tagesSatz } from "@/lib/tagestext";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

// In „Tagesminuten“ wie die Zuordnung in lib/ableitungen.ts (tageszeitVon): Zeiten vor 6 Uhr gehören
// zur Nacht und zählen als 24:00 + Uhrzeit (00:30 → 1470), siehe tagesminuten() in zeitleiste.tsx
const GRENZEN: Record<string, [number, number]> = {
  morgens: [6 * 60, 12 * 60],
  nachmittags: [12 * 60, 18 * 60],
  abends: [18 * 60, 23 * 60],
  nachts: [23 * 60, 30 * 60],
};

function tagHref(tag: string, heute: string) {
  return tag === heute ? "/heute" : `/tag/${tag}`;
}

/**
 * pfad: kanonischer Pfad der Seite („/heute“ oder „/tag/2026-11-12“) – für Brotkrumen und ItemList.
 * Rendert ohne Suspense direkt ins erste HTML (Daten aus dem Cache): H1, Tages-Satz und die Liste stehen als Text da.
 */
export async function Tagesplaner({ tag, pfad }: { tag?: string; pfad: string }) {
  const pool = await eventPoolLaden();
  const { heute } = pool;
  // Vergangene Tage: Der Pool beginnt mit heute – nie die heutigen Events unter ein altes Datum schreiben
  if (tag && tag < heute) return <VergangenerTag tag={tag} heute={heute} pfad={pfad} />;
  const d = tag ?? heute;
  const istHeute = d === heute;
  const titel = istHeute ? "Heute" : d === plusTage(heute, 1) ? "Morgen" : WT_LANG[wochentag(d)];
  const untertitel = istHeute || d === plusTage(heute, 1) ? `${WT_LANG[wochentag(d)]}, ${tagMonat(d)}` : tagMonat(d);

  const events = filtern(pool.events, { von: d, bis: d }).sort(nachZeit);
  const ganztags = events.filter((e) => !e.uhrzeit);
  const abschnitte: Abschnitt[] = TAGESZEITEN.map((t) => ({
    name: t.name,
    bereich: t.bereich,
    icon: t.icon,
    von: GRENZEN[t.key][0],
    bis: GRENZEN[t.key][1],
    // Events nach Mitternacht (vor 6 Uhr) laufen unter "Nachts" ans Ende.
    // Gebündelte Termine (z.B. 11 und 19 Uhr) erscheinen in jedem passenden Abschnitt.
    events: events.filter((e) => tageszeiten(e).includes(t.key)).sort((a, b) => {
      const n = (x: string | null) => (x && x < "06:00" ? `3${x}` : `1${x}`);
      return n(ersteUhrzeitIn(a, t.key)).localeCompare(n(ersteUhrzeitIn(b, t.key)));
    }),
  }));
  if (ganztags.length) abschnitte.unshift({ name: "Ganztägig", bereich: "ohne feste Uhrzeit", icon: "calendar_today", von: -1, bis: -1, events: ganztags });

  // Satz aus denselben Zeilen, die die Liste zeigt (gebündelte Termine zählen einmal) – nicht bei Beispieldaten
  // (Ausfall der Datenbank): die wären keine echte Zählung
  const satz = pool.quelle === "supabase" ? tagesSatz(d, events) : null;
  const stand = pool.quelle === "supabase" ? standText(pool.jetzt) : null;
  const jsonLd = eventListeJsonLd(
    SITE_URL,
    `Events in Düsseldorf am ${datumText(d)}`,
    [{ name: "Start", pfad: "/" }, { name: istHeute ? "Heute" : `Events am ${datumText(d)}`, pfad }],
    events,
  );

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <div className="tagleiste">
        <div className="container tagleiste__inner">
          <Link href={tagHref(plusTage(d, -1), heute)} className="icon-btn" aria-label="Vorheriger Tag" aria-disabled={istHeute ? "true" : undefined} tabIndex={istHeute ? -1 : undefined}>
            <Icon name="chevron_left" />
          </Link>
          <div className="tagleiste__mitte">
            <h1 className="d">{titel}</h1>
            <span>
              {untertitel} · {events.length} Events
            </span>
          </div>
          <Link href={tagHref(plusTage(d, 1), heute)} className="icon-btn" aria-label="Nächster Tag">
            <Icon name="chevron_right" />
          </Link>
        </div>
      </div>
      <div className="container planer">
        {satz && <p className="tagesatz">{satz}</p>}
        {stand && <p className="tagesatz__stand muted">{stand}</p>}
        {events.length ? (
          <Zeitleiste abschnitte={abschnitte} istHeute={istHeute} />
        ) : (
          <div className="sektion">
            <Leer titel={istHeute ? "Heute ist es ruhig." : "Für diesen Tag ist noch nichts eingetragen."}>
              <Link href="/wochenende" className="link">
                Schau mal ins Wochenende <Icon name="arrow_forward" />
              </Link>
            </Leer>
          </div>
        )}
      </div>
    </>
  );
}

/** Ein vergangener Tag: ehrlich als vorbei zeigen (die Seite ist noindex, siehe app/tag/[datum]/page.tsx). */
function VergangenerTag({ tag, heute, pfad }: { tag: string; heute: string; pfad: string }) {
  const jsonLd = eventListeJsonLd(SITE_URL, "", [{ name: "Start", pfad: "/" }, { name: `Events am ${datumText(tag)}`, pfad }], []);
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <div className="tagleiste">
        <div className="container tagleiste__inner">
          <span className="icon-btn" aria-hidden />
          <div className="tagleiste__mitte">
            <h1 className="d">{WT_LANG[wochentag(tag)]}</h1>
            <span>{datumText(tag)}</span>
          </div>
          <Link href={tagHref(plusTage(tag, 1), heute)} className="icon-btn" aria-label="Nächster Tag">
            <Icon name="chevron_right" />
          </Link>
        </div>
      </div>
      <div className="container planer sektion">
        <p className="tagesatz">Der {datumText(tag)} ist vorbei.</p>
        <Leer titel="Dieser Tag liegt in der Vergangenheit.">
          <Link href="/heute" className="link">
            Was heute in Düsseldorf los ist <Icon name="arrow_forward" />
          </Link>
        </Leer>
      </div>
    </>
  );
}

export function TagesplanerSkeleton() {
  return (
    <>
      <div className="tagleiste">
        <div className="container tagleiste__inner" style={{ height: 82 }} />
      </div>
      <div className="container planer sektion">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="skeleton" style={{ height: 84, marginBottom: 12, borderRadius: 16 }} />
        ))}
      </div>
    </>
  );
}
