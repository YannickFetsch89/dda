// Stadtteil-Clustering: schematische Karte der 10 Stadtbezirke + Stadtteile mit Event-Anzahl
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Icon, ListenZeile, SkeletonKarten } from "@/components/karten";
import { eventPoolLaden } from "@/lib/daten";
import { filtern, nachBezirken } from "@/lib/ableitungen";
import { zeitraumAuflösen } from "@/lib/datum";
import { kategorie, katStil } from "@/lib/kategorien";
import { OHNE_ZUORDNUNG, stadtteilName } from "@/lib/stadtteile";

export const metadata: Metadata = {
  title: "Events nach Stadtteil",
  description: "Was geht in deinem Veedel? Alle Events in Düsseldorf nach Stadtbezirk und Stadtteil.",
};

const ZEITRAEUME = [
  { key: "heute", label: "Heute" },
  { key: "wochenende", label: "Wochenende" },
  { key: "woche", label: "Diese Woche" },
  { key: "monat", label: "30 Tage" },
];

export default function Stadtteile(props: PageProps<"/stadtteile">) {
  return (
    <div className="container">
      <div className="seitentitel">
        <h1 className="d">Nach Stadtteil</h1>
      </div>
      <Suspense fallback={<div className="sektion"><SkeletonKarten anzahl={4} /></div>}>
        <StadtteileInhalt searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

async function StadtteileInhalt({ searchParams }: Pick<PageProps<"/stadtteile">, "searchParams">) {
  const sp = await searchParams;
  const pool = await eventPoolLaden();
  const z = zeitraumAuflösen(typeof sp.datum === "string" ? sp.datum : "woche", pool.heute);
  const events = filtern(pool.events, { von: z.von, bis: z.bis });
  const { bezirke, ohneZuordnung, umland } = nachBezirken(events);
  const max = Math.max(1, ...bezirke.map((b) => b.anzahl));
  const radius = (anzahl: number) => 3 + Math.sqrt(anzahl / max) * 6.5;
  const zugeordnet = events.length - ohneZuordnung;

  return (
    <>
      <div className="filterleiste" aria-label="Zeitraum">
        {ZEITRAEUME.map((o) => (
          <Link key={o.key} href={`/stadtteile?datum=${o.key}`} className="chip" aria-current={z.key === o.key ? "true" : undefined} scroll={false}>
            {o.label}
          </Link>
        ))}
      </div>
      <p className="zuordnungs-hinweis" style={{ marginTop: 12 }}>
        {events.length} Events {z.label.toLowerCase()}, davon {zugeordnet} einem Stadtteil zugeordnet ({events.length ? Math.round((zugeordnet / events.length) * 100) : 0} %).
      </p>

      <div className="sektion stadtteil-raster">
        <div className="karte-schema">
          <svg viewBox="0 0 100 100" role="img" aria-label="Schematische Karte der Düsseldorfer Stadtbezirke mit Anzahl der Events">
            {/* Rhein, stark vereinfacht */}
            <path
              d="M30 -2 C 26 14, 36 24, 34 32 C 32 40, 24 46, 30 54 C 36 62, 44 64, 42 74 C 40 84, 48 92, 46 102"
              fill="none"
              stroke="#457B9D"
              strokeOpacity="0.28"
              strokeWidth="5"
              strokeLinecap="round"
            />
            <text x="22" y="66" fontSize="2.6" fill="#457B9D" fillOpacity="0.8" fontStyle="italic" transform="rotate(-62 22 66)">
              Rhein
            </text>
            {bezirke.map((b) => {
              const r = radius(b.anzahl);
              return (
                <a key={b.nr} href={`#bezirk-${b.nr}`} className="karte-schema__blase">
                  <title>{`${b.name}: ${b.anzahl} Events`}</title>
                  <circle cx={b.x} cy={b.y} r={r} className={b.anzahl ? "voll" : ""} fill={b.anzahl ? "#1B2540" : "#EDF0F4"} stroke="#FFFFFF" strokeWidth="0.6" />
                  <text x={b.x} y={b.y + 1.2} textAnchor="middle" fontSize={r > 6 ? 3.6 : 2.8} fill={b.anzahl ? "#C9A84C" : "#A0AEC0"} fontFamily="var(--font-dm-serif), serif" fontStyle="italic">
                    {b.anzahl}
                  </text>
                </a>
              );
            })}
            {/* Beschriftungen in eigenem Durchgang, damit kein Kreis sie verdeckt */}
            {bezirke.map((b) => (
              <text key={b.nr} x={b.x} y={b.y + radius(b.anzahl) + 3} textAnchor="middle" fontSize="2.3" fontWeight="600" fill="currentColor" pointerEvents="none" style={{ color: "var(--ddd-text-body)", paintOrder: "stroke", stroke: "var(--ddd-surface)", strokeWidth: 0.8 }}>
                {b.name}
              </text>
            ))}
          </svg>
          <span className="karte-schema__legende">Kreisgröße = Anzahl Events · schematisch, nicht maßstabsgetreu</span>
        </div>

        <div className="bezirke">
          {[...bezirke]
            .sort((a, b) => b.anzahl - a.anzahl)
            .map((b) => (
              <section key={b.nr} id={`bezirk-${b.nr}`} className="bezirk">
                <div className="bezirk__kopf">
                  <span className="bezirk__nr">{b.nr}</span>
                  <h2 className="d">{b.name}</h2>
                  <span>{b.anzahl}</span>
                </div>
                {b.anzahl > 0 && (
                  <div className="katbalken" aria-label="Verteilung nach Kategorie">
                    {b.kategorien.map((k) => (
                      <span key={k.slug} style={{ ...katStil(k.slug), flex: k.anzahl }} title={`${kategorie(k.slug).name}: ${k.anzahl}`} />
                    ))}
                  </div>
                )}
                {b.stadtteile.length > 0 ? (
                  <div className="kachel-raster">
                    {b.stadtteile.map((s) => (
                      <Link key={s.name} className="kachel" href={`/entdecken?stadtteil=${encodeURIComponent(s.name)}&datum=${z.key}`}>
                        <span>{stadtteilName(s.name)}</span>
                        <span>{s.anzahl}</span>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="zuordnungs-hinweis">Keine Events in diesem Zeitraum.</p>
                )}
                {b.top.length > 0 && (
                  <div>
                    {b.top.map((e) => (
                      <ListenZeile key={e.id} e={e} zeit={e.datum === pool.heute ? e.uhrzeit ?? "heute" : `${e.datum.slice(8, 10)}.${e.datum.slice(5, 7)}.`} />
                    ))}
                  </div>
                )}
                {b.anzahl > 3 && (
                  <Link className="link" href={`/entdecken?bezirk=${b.nr}&datum=${z.key}`}>
                    Alle {b.anzahl} im Bezirk <Icon name="arrow_forward" />
                  </Link>
                )}
              </section>
            ))}
          {(ohneZuordnung > 0 || umland.length > 0) && (
            <section className="bezirk">
              <div className="bezirk__kopf">
                <span className="bezirk__nr">?</span>
                <h2 className="d">Weitere</h2>
                <span>{ohneZuordnung + umland.reduce((s, u) => s + u.anzahl, 0)}</span>
              </div>
              <div className="kachel-raster">
                {umland.map((u) => (
                  <Link key={u.name} className="kachel" href={`/entdecken?stadtteil=${encodeURIComponent(u.name)}&datum=${z.key}`}>
                    <span>{u.name}</span>
                    <span>{u.anzahl}</span>
                  </Link>
                ))}
                {ohneZuordnung > 0 && (
                  <Link className="kachel" href={`/entdecken?stadtteil=${encodeURIComponent(OHNE_ZUORDNUNG)}&datum=${z.key}`}>
                    <span>{OHNE_ZUORDNUNG}</span>
                    <span>{ohneZuordnung}</span>
                  </Link>
                )}
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  );
}
