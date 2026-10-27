// Tagesplaner (Design-Ansicht 04), genutzt von /heute und /tag/[datum]
import Link from "next/link";
import { Icon, Leer } from "./karten";
import { Zeitleiste, type Abschnitt } from "./zeitleiste";
import { eventPoolLaden } from "@/lib/daten";
import { TAGESZEITEN, filtern, nachZeit, tageszeit } from "@/lib/ableitungen";
import { WT_LANG, plusTage, tagMonat, wochentag } from "@/lib/datum";

const GRENZEN: Record<string, [number, number]> = {
  morgens: [0, 12 * 60],
  nachmittags: [12 * 60, 18 * 60],
  abends: [18 * 60, 23 * 60],
  nachts: [23 * 60, 24 * 60],
};

function tagHref(tag: string, heute: string) {
  return tag === heute ? "/heute" : `/tag/${tag}`;
}

export async function Tagesplaner({ tag }: { tag?: string }) {
  const pool = await eventPoolLaden();
  const { heute } = pool;
  const d = tag && tag >= heute ? tag : heute;
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
    // Events nach Mitternacht (vor 6 Uhr) laufen unter "Nachts" ans Ende
    events: events.filter((e) => tageszeit(e) === t.key).sort((a, b) => {
      const n = (x: string | null) => (x && x < "06:00" ? `3${x}` : `1${x}`);
      return n(a.uhrzeit).localeCompare(n(b.uhrzeit));
    }),
  }));
  if (ganztags.length) abschnitte.unshift({ name: "Ganztägig", bereich: "ohne feste Uhrzeit", icon: "calendar_today", von: -1, bis: -1, events: ganztags });

  return (
    <>
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
