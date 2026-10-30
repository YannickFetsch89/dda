// Restaurant & Café Guide – Übersichtsseite
import type { Metadata } from "next";
import { Suspense } from "react";
import { OrtKartenGrid } from "@/components/ort-karten";
import { Icon } from "@/components/karten";
import { orteLaden, orteNachStadtteil } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

export const metadata: Metadata = {
  title: "Restaurants & Cafés in Düsseldorf – DiesDasDüsseldorf",
  description: "Kuratierte Restaurant- und Café-Empfehlungen in Düsseldorf. Entdecke die besten Adressen nach Stadtteil, Küche und Preisniveau.",
};

type SP = Record<string, string | string[] | undefined>;

function einzeln(sp: SP): Record<string, string | undefined> {
  return Object.fromEntries(Object.entries(sp).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]));
}

function filterUrl(aktuell: Record<string, string | undefined>, aenderung: Record<string, string | undefined>): string {
  const p = new URLSearchParams();
  const neu = { ...aktuell, ...aenderung };
  Object.entries(neu).forEach(([k, v]) => { if (v) p.set(k, v); });
  const qs = p.toString();
  return qs ? `/restaurants?${qs}` : "/restaurants";
}

function filterOrte(orte: DddOrt[], params: Record<string, string | undefined>): DddOrt[] {
  let ergebnis = orte;

  if (params.typ === "cafe") ergebnis = ergebnis.filter((o) => o.typ === "cafe");
  else if (params.typ === "restaurant") ergebnis = ergebnis.filter((o) => o.typ === "restaurant");

  if (params.stadtteil) ergebnis = ergebnis.filter((o) => o.stadtteil === params.stadtteil);

  if (params.preis) ergebnis = ergebnis.filter((o) => o.preis_niveau === params.preis);

  if (params.tag) ergebnis = ergebnis.filter((o) => o.tags.includes(params.tag!));

  return ergebnis;
}

async function Inhalt({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = einzeln(await searchParams);
  const alle = await orteLaden(["restaurant", "cafe"]);
  const stadtteile = await orteNachStadtteil(["restaurant", "cafe"]);
  const gefiltert = filterOrte(alle, sp);

  const restaurants = alle.filter((o) => o.typ === "restaurant").length;
  const cafes = alle.filter((o) => o.typ === "cafe").length;

  const alleTags = Array.from(new Set(alle.flatMap((o) => o.tags))).sort();

  return (
    <>
      <div className="seitentitel">
        <h1 className="d">Restaurants & Cafés</h1>
        <p className="seitentitel__sub">
          {alle.length > 0
            ? `${restaurants} Restaurants und ${cafes} Cafés – kuratiert für Düsseldorf`
            : "Kuratierte Empfehlungen für Düsseldorf. Bald verfügbar!"}
        </p>
      </div>

      {/* Filter */}
      <nav className="filter-leiste" aria-label="Filter">
        <div className="filter-leiste__gruppe">
          <span className="filter-leiste__label">Typ</span>
          <a href="/restaurants" className={`chip ${!sp.typ ? "chip--aktiv" : ""}`}>Alle</a>
          <a href={filterUrl(sp, { typ: sp.typ === "restaurant" ? undefined : "restaurant" })} className={`chip ${sp.typ === "restaurant" ? "chip--aktiv" : ""}`}>
            <Icon name="restaurant" /> Restaurants
          </a>
          <a href={filterUrl(sp, { typ: sp.typ === "cafe" ? undefined : "cafe" })} className={`chip ${sp.typ === "cafe" ? "chip--aktiv" : ""}`}>
            <Icon name="local_cafe" /> Cafés
          </a>
        </div>

        {stadtteile.length > 0 && (
          <div className="filter-leiste__gruppe">
            <span className="filter-leiste__label">Stadtteil</span>
            <a href={filterUrl(sp, { stadtteil: undefined })} className={`chip ${!sp.stadtteil ? "chip--aktiv" : ""}`}>Alle</a>
            {stadtteile.slice(0, 10).map(({ stadtteil, anzahl }) => (
              <a key={stadtteil} href={filterUrl(sp, { stadtteil: sp.stadtteil === stadtteil ? undefined : stadtteil })} className={`chip ${sp.stadtteil === stadtteil ? "chip--aktiv" : ""}`}>
                {stadtteil} <span className="chip__anzahl">{anzahl}</span>
              </a>
            ))}
          </div>
        )}

        {alleTags.length > 0 && (
          <div className="filter-leiste__gruppe">
            <span className="filter-leiste__label">Tags</span>
            {alleTags.slice(0, 12).map((tag) => (
              <a key={tag} href={filterUrl(sp, { tag: sp.tag === tag ? undefined : tag })} className={`chip ${sp.tag === tag ? "chip--aktiv" : ""}`}>
                {tag}
              </a>
            ))}
          </div>
        )}

        <div className="filter-leiste__gruppe">
          <span className="filter-leiste__label">Preis</span>
          <a href={filterUrl(sp, { preis: undefined })} className={`chip ${!sp.preis ? "chip--aktiv" : ""}`}>Alle</a>
          {(["€", "€€", "€€€"] as const).map((p) => (
            <a key={p} href={filterUrl(sp, { preis: sp.preis === p ? undefined : p })} className={`chip ${sp.preis === p ? "chip--aktiv" : ""}`}>
              {p}
            </a>
          ))}
        </div>
      </nav>

      {/* Ergebnisse */}
      <div className="sektion">
        {gefiltert.length !== alle.length && (
          <p className="filter-status">
            {gefiltert.length} {gefiltert.length === 1 ? "Ergebnis" : "Ergebnisse"}
            {sp.stadtteil ? ` in ${sp.stadtteil}` : ""}
            {sp.typ ? ` (${sp.typ === "cafe" ? "Cafés" : "Restaurants"})` : ""}
          </p>
        )}
        <OrtKartenGrid orte={gefiltert} />
      </div>
    </>
  );
}

export default function RestaurantsSeite(props: { searchParams: Promise<SP> }) {
  return (
    <div className="container">
      <Suspense
        fallback={
          <div className="seitentitel">
            <h1 className="d">Restaurants & Cafés</h1>
            <p className="seitentitel__sub">Lädt Empfehlungen …</p>
          </div>
        }
      >
        <Inhalt searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}
