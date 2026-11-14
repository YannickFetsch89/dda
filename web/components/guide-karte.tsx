"use client";
// Kartenansicht der Guides (Design-Handoff v2, Ansicht 13): links kompakte Liste, rechts Karte mit Pins.
// Alles kommt vom eigenen Server: Kartendaten (PMTiles, OpenStreetMap), Schriften, Symbole, MapLibre-Worker
// und Fotos – der Browser spricht mit keinem fremden Dienst, daher keine Einwilligung nötig.
import * as maplibregl from "maplibre-gl"; // MapLibre 6: nur benannte Exporte
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";
import { layers, namedFlavor } from "@protomaps/basemaps";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export interface KartenOrt {
  id: string;
  name: string;
  typLabel: string;
  icon: string;
  stadtteil: string | null;
  preis: string | null;
  rating: string | null;
  anzahl: string | null;
  bild: string | null;
  href: string;
  lat: number;
  lng: number;
  /** Nur Club-Hub: Empfehlungsstufe → Pin-Farbe (a = Top, b = empfohlen, c = weitere) */
  stufe?: "a" | "b" | "c";
  stufeLabel?: string;
  /** Nur Spielplätze: Altersgruppe → Pin-Farbe (unbekannt = neutral) und Text für Liste/Popup */
  alter?: "0-3" | "3-6" | "6-12" | "alle" | "unbekannt";
  alterLabel?: string;
}

const START = { center: [6.7735, 51.2277] as [number, number], zoom: 12 };
let protokollRegistriert = false;

function kartenStil(dunkel: boolean): maplibregl.StyleSpecification {
  const basis = window.location.origin;
  return {
    version: 8,
    glyphs: `${basis}/karte/fonts/{fontstack}/{range}.pbf`,
    sprite: `${basis}/karte/sprites/${dunkel ? "dark" : "light"}`,
    sources: {
      protomaps: {
        type: "vector",
        url: `pmtiles://${basis}/karte/region.pmtiles`,
        attribution: '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap-Mitwirkende</a>',
      },
    },
    layers: layers("protomaps", namedFlavor(dunkel ? "dark" : "light"), { lang: "de" }),
  };
}

function istDunkel(): boolean {
  return document.documentElement.dataset.theme === "dark";
}

/** Pin als DOM-Element (Tropfenform mit Icon, siehe 00_global/components.md → Karten). */
function pinElement(o: KartenOrt): HTMLButtonElement {
  const pin = document.createElement("button");
  pin.type = "button";
  pin.className = o.stufe ? `gd-pin gd-pin--stufe gd-pin--stufe-${o.stufe}` : o.alter ? `gd-pin gd-pin--alter gd-pin--alter-${o.alter}` : "gd-pin";
  const zusatz = o.stufeLabel ?? o.alterLabel;
  pin.setAttribute("aria-label", zusatz ? `${o.name} (${zusatz})` : o.name);
  const icon = document.createElement("span");
  icon.className = "icon";
  // Eigene SVG-Piktogramme („sp:…“, CSS-Maske über data-icon) statt Ligatur-Text
  if (o.icon.startsWith("sp:")) icon.dataset.icon = o.icon;
  else icon.textContent = o.icon;
  pin.appendChild(icon);
  return pin;
}

/** Vorschaubild in der Liste; fehlt es oder lädt es nicht (404), steht das Typ-Icon auf hellem Grund. */
function ListenBild({ bild, icon }: { bild: string | null; icon: string }) {
  const [fehler, setFehler] = useState<string | null>(null);
  const zeigen = bild && fehler !== bild;
  return (
    <span className="gd-kompakt__bild">
      {zeigen ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={bild} alt="" loading="lazy" onError={() => setFehler(bild)} />
      ) : (
        <span className="icon" aria-hidden data-icon={icon} />
      )}
    </span>
  );
}

/** Popup-Inhalt per DOM (Texte über textContent – keine HTML-Injektion aus Datenbankwerten). */
function popupInhalt(o: KartenOrt): HTMLElement {
  const box = document.createElement("a");
  box.href = o.href;
  box.className = "ddd-pop";
  if (o.bild) {
    const img = document.createElement("img");
    img.src = o.bild;
    img.alt = "";
    img.loading = "lazy";
    // Bild nicht ladbar (z. B. Illustration fehlt): Popup ohne Bild statt kaputtem Symbol
    img.onerror = () => img.remove();
    box.appendChild(img);
  }
  const text = document.createElement("span");
  text.className = "ddd-pop__text";
  const typ = document.createElement("span");
  typ.className = "ddd-pop__typ";
  const zusatz = o.stufeLabel ?? o.alterLabel;
  typ.textContent = zusatz ? `${o.typLabel} · ${zusatz}` : o.typLabel;
  const name = document.createElement("span");
  name.className = "ddd-pop__name d";
  name.textContent = o.name;
  const fuss = document.createElement("span");
  fuss.className = "ddd-pop__fuss";
  fuss.textContent = `${o.rating ? `★ ${o.rating}` : ""}`;
  const mehr = document.createElement("span");
  mehr.className = "ddd-pop__mehr";
  mehr.textContent = "Details →";
  fuss.appendChild(mehr);
  text.append(typ, name, fuss);
  box.appendChild(text);
  return box;
}

const KEINE: KartenOrt[] = [];

/** Entfernung in Metern (Haversine) – nur im Browser, für „In der Nähe“. */
function abstand(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const r = (x: number) => (x * Math.PI) / 180;
  const h = Math.sin(r(b.lat - a.lat) / 2) ** 2 + Math.cos(r(a.lat)) * Math.cos(r(b.lat)) * Math.sin(r(b.lng - a.lng) / 2) ** 2;
  return 2 * 6371000 * Math.asin(Math.sqrt(h));
}
const abstandText = (m: number) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1).replace(".", ",")} km`);

/**
 * `orte` ist null, solange die Punkte noch nachgeladen werden (siehe guide-karte-lazy.tsx).
 * `naehe` (Spielplätze, E8): Knopf „In der Nähe“ – fragt den Standort erst nach Klick ab, rechnet nur im Browser,
 * speichert und sendet nichts. Ohne Freigabe bleibt die Reihenfolge.
 */
export default function GuideKarte({ orte: geladen, ladefehler = false, naehe = false }: { orte: KartenOrt[] | null; ladefehler?: boolean; naehe?: boolean }) {
  const roh = geladen ?? KEINE;
  const [standort, setStandort] = useState<{ lat: number; lng: number } | null>(null);
  const [standortHinweis, setStandortHinweis] = useState<string | null>(null);
  const standortRef = useRef<maplibregl.Marker | null>(null);
  const orte = useMemo(
    () => (standort ? [...roh].sort((a, b) => abstand(standort, a) - abstand(standort, b)) : roh),
    [roh, standort],
  );
  const kartenRef = useRef<HTMLDivElement>(null);
  const listeRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef(new Map<string, { marker: maplibregl.Marker; el: HTMLButtonElement }>());
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [gewaehlt, setGewaehlt] = useState<string | null>(null);
  const [bereich, setBereich] = useState<maplibregl.LngLatBounds | null>(null);
  const [bewegt, setBewegt] = useState(false);
  const [fehler, setFehler] = useState(false);
  // Inhalt der zuletzt gesetzten Pins – neu aufbauen nur, wenn sich die Orte wirklich ändern
  // (nicht bei jeder neuen Array-Instanz, z.B. nach Sortierwechsel), damit Ausschnitt/Bereich erhalten bleiben
  const pinSchluessel = useRef("");

  const sichtbar = useMemo(
    () => (bereich ? orte.filter((o) => bereich.contains([o.lng, o.lat])) : orte),
    [orte, bereich],
  );

  const auswaehlen = useCallback(
    (id: string, ausListe: boolean) => {
      const map = mapRef.current;
      const o = orte.find((x) => x.id === id);
      if (!map || !o) return;
      setGewaehlt(id);
      popupRef.current?.remove();
      // Popup immer über dem Pin (Pin-Spitze sitzt auf dem Ort, der Pin ist ~40px hoch)
      popupRef.current = new maplibregl.Popup({ closeButton: false, anchor: "bottom", offset: [0, -42], maxWidth: "240px", className: "ddd-pop-huelle" })
        .setLngLat([o.lng, o.lat])
        .setDOMContent(popupInhalt(o))
        .addTo(map);
      // Ort unterhalb der Kartenmitte platzieren, damit das Popup darüber Platz hat
      const versatz: [number, number] = [0, Math.min(140, map.getContainer().clientHeight / 2 - 30)];
      if (ausListe) {
        map.flyTo({ center: [o.lng, o.lat], zoom: Math.max(map.getZoom(), 15), offset: versatz, duration: 600 });
      } else {
        map.easeTo({ center: [o.lng, o.lat], offset: versatz, duration: 400 });
        // Nur am Desktop (Liste neben der Karte, eigener Scrollbereich) zum Eintrag scrollen. Unter 1200 px
        // steht die Liste unter der Karte – dort würde die ganze Seite wegspringen; es geht nur das Popup auf.
        if (window.matchMedia("(min-width: 1200px)").matches) {
          listeRef.current?.querySelector(`[data-id="${CSS.escape(id)}"]`)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
      }
    },
    [orte],
  );

  // Karte einmalig aufbauen
  useEffect(() => {
    if (!kartenRef.current) return;
    if (!protokollRegistriert) {
      maplibregl.addProtocol("pmtiles", new Protocol().tile);
      maplibregl.setWorkerUrl(`${window.location.origin}/karte/maplibre-gl-worker.mjs`);
      protokollRegistriert = true;
    }
    const map = new maplibregl.Map({
      container: kartenRef.current,
      style: kartenStil(istDunkel()),
      center: START.center,
      zoom: START.zoom,
      minZoom: 9,
      maxZoom: 18,
      maxBounds: [[6.55, 51.08], [6.99, 51.39]], // = Ausschnitt in region.pmtiles, außerhalb gibt es keine Kacheln
      scrollZoom: false, // laut Design: Scrollzoom aus (Seite soll weiter scrollen)
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.on("dragend", () => setBewegt(true));
    // Nur vom Nutzer ausgelöstes Zoomen zählt (nicht fitBounds/flyTo aus dem Code)
    map.on("zoomend", (e: { originalEvent?: unknown }) => { if (e.originalEvent) setBewegt(true); });
    // Kartendaten fehlen (z.B. region.pmtiles nicht auf dem Server) → Hinweis statt leerer Fläche.
    // Nur ein Fehler, bevor die Kartenquelle je Daten geliefert hat, zählt – einzelne abgebrochene
    // Kachel-Abrufe danach (Zoomen, Abbau im Strict Mode) lösen den Hinweis nicht aus.
    let aktiv = true;
    let quelleErreichbar = false;
    // "visibility" kommt schon vor dem ersten Abruf – erst Metadaten oder eine Kachel beweisen, dass die Datei da ist
    map.on("sourcedata", (e: { sourceId?: string; sourceDataType?: string; tile?: unknown }) => {
      if (!aktiv || e.sourceId !== "protomaps" || (e.sourceDataType !== "metadata" && !e.tile)) return;
      quelleErreichbar = true;
      setFehler(false);
    });
    map.on("error", (e: { sourceId?: string; error?: { message?: string } }) => {
      if (!aktiv || quelleErreichbar) return;
      if (e.sourceId === "protomaps" || /pmtiles/i.test(e.error?.message ?? "")) setFehler(true);
    });
    mapRef.current = map;

    // Nach Layout-Wechseln Größe neu berechnen (sonst zeigt die Karte nur ein Stück)
    const beobachter = new ResizeObserver(() => map.resize());
    beobachter.observe(kartenRef.current);

    // Dark Mode folgen
    const themen = new MutationObserver(() => map.setStyle(kartenStil(istDunkel())));
    themen.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

    const marker = markerRef.current;
    return () => {
      aktiv = false;
      beobachter.disconnect();
      themen.disconnect();
      map.remove();
      mapRef.current = null;
      marker.clear();
      pinSchluessel.current = "";
    };
  }, []);

  // Pins setzen, wenn sich die Orte ändern (Filter)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const schluessel = orte.map((o) => `${o.id}@${o.lat},${o.lng}`).sort().join("|");
    if (schluessel === pinSchluessel.current) return;
    pinSchluessel.current = schluessel;
    popupRef.current?.remove();
    popupRef.current = null;
    setGewaehlt(null);
    for (const { marker } of markerRef.current.values()) marker.remove();
    markerRef.current.clear();
    for (const o of orte) {
      const el = pinElement(o);
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        auswaehlen(o.id, false);
      });
      const marker = new maplibregl.Marker({ element: el, anchor: "bottom" }).setLngLat([o.lng, o.lat]).addTo(map);
      markerRef.current.set(o.id, { marker, el });
    }
    if (orte.length > 1) {
      const grenzen = new maplibregl.LngLatBounds();
      for (const o of orte) grenzen.extend([o.lng, o.lat]);
      map.fitBounds(grenzen, { padding: 48, maxZoom: 15, duration: 0 });
    } else if (orte.length === 1) {
      map.jumpTo({ center: [orte[0].lng, orte[0].lat], zoom: 15 });
    }
    setBereich(null);
    setBewegt(false);
  }, [orte, auswaehlen]);

  // Bei "In diesem Bereich suchen" nur die Pins der Liste zeigen
  useEffect(() => {
    const ids = new Set(sichtbar.map((o) => o.id));
    for (const [id, { el }] of markerRef.current) el.classList.toggle("gd-pin--aus", !ids.has(id));
    if (gewaehlt && !ids.has(gewaehlt)) {
      popupRef.current?.remove();
      popupRef.current = null;
    }
  }, [sichtbar, gewaehlt]);

  // Eigener Standort als Navy-Kreis; Karte auf Standort und die nächsten Plätze ausrichten
  useEffect(() => {
    const map = mapRef.current;
    standortRef.current?.remove();
    standortRef.current = null;
    if (!map || !standort) return;
    const punkt = document.createElement("span");
    punkt.className = "gd-standort";
    punkt.setAttribute("aria-label", "Dein Standort");
    standortRef.current = new maplibregl.Marker({ element: punkt }).setLngLat([standort.lng, standort.lat]).addTo(map);
    const grenzen = new maplibregl.LngLatBounds();
    grenzen.extend([standort.lng, standort.lat]);
    for (const o of orte.slice(0, 5)) grenzen.extend([o.lng, o.lat]);
    map.fitBounds(grenzen, { padding: 60, maxZoom: 15, duration: 600 });
    listeRef.current?.scrollTo({ top: 0 });
  }, [standort, orte]);

  const standortHolen = () => {
    if (!("geolocation" in navigator)) {
      setStandortHinweis("Dein Browser kann den Standort nicht bestimmen. Die Liste bleibt in der bisherigen Reihenfolge.");
      return;
    }
    setStandortHinweis("Standort wird bestimmt …");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setStandort({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setStandortHinweis(null);
      },
      () => setStandortHinweis("Ohne Standortfreigabe bleibt die Liste in der bisherigen Reihenfolge."),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  };

  // Ausgewählten Pin hervorheben
  useEffect(() => {
    for (const [id, { el, marker }] of markerRef.current) {
      const an = id === gewaehlt;
      el.classList.toggle("gd-pin--an", an);
      marker.getElement().style.zIndex = an ? "2" : "";
    }
  }, [gewaehlt]);

  return (
    <div className="gd-kartenansicht">
      <div className="gd-kartenliste" ref={listeRef} role="list" aria-label="Orte auf der Karte">
        {naehe && (
          <div className="gd-kartenliste__hinweis gd-naehe">
            <button type="button" className={`gd-naehe__knopf ${standort ? "is-aktiv" : ""}`} onClick={standort ? () => setStandort(null) : standortHolen} aria-pressed={!!standort}>
              <span className="icon" aria-hidden data-icon={standort ? "close" : "my_location"} />
              {standort ? "Nähe-Sortierung beenden" : "In der Nähe"}
            </button>
            <span className="muted">{standortHinweis ?? (standort ? "Sortiert nach Entfernung – dein Standort bleibt in deinem Browser." : "Sortiert nach Empfehlung. Für die Nähe fragt dein Browser nach deinem Standort.")}</span>
          </div>
        )}
        {bereich && (
          <div className="gd-kartenliste__hinweis">
            {sichtbar.length} {sichtbar.length === 1 ? "Ort" : "Orte"} in diesem Bereich ·{" "}
            <button type="button" onClick={() => setBereich(null)}>Alle zeigen</button>
          </div>
        )}
        {sichtbar.map((o) => (
          <div
            key={o.id} role="listitem" data-id={o.id}
            className={`gd-kompakt ${o.alter ? `gd-kompakt--alter-${o.alter}` : ""} ${o.id === gewaehlt ? "gd-kompakt--an" : ""}`}
            onMouseEnter={() => markerRef.current.get(o.id)?.el.classList.add("gd-pin--puls")}
            onMouseLeave={() => markerRef.current.get(o.id)?.el.classList.remove("gd-pin--puls")}
          >
            <button type="button" className="gd-kompakt__knopf" onClick={() => auswaehlen(o.id, true)} aria-pressed={o.id === gewaehlt}>
              <ListenBild bild={o.bild} icon={o.icon} />
              <span className="gd-kompakt__text">
                <span className="gd-typ">
                  {o.stufe ? <span className={`cl-stufe__punkt cl-stufe__punkt--${o.stufe}`} aria-hidden />
                    : o.alter ? <span className={`sp-punkt sp-punkt--${o.alter}`} aria-hidden />
                    : <span className="icon" aria-hidden data-icon={o.icon} />}
                  {o.stufeLabel ?? (o.alterLabel ? `${o.typLabel} · ${o.alterLabel}` : o.typLabel)}
                </span>
                <span className="gd-kompakt__name d">{o.name}</span>
                <span className="gd-kompakt__meta">
                  {o.rating && <span className="gd-bewertung"><span className="icon is-active" aria-hidden data-icon="star" /><b>{o.rating}</b>{o.anzahl && <span className="muted">({o.anzahl})</span>}</span>}
                  <span className="muted">{[o.stadtteil, standort ? abstandText(abstand(standort, o)) : null, o.preis].filter(Boolean).join(" · ")}</span>
                </span>
              </span>
            </button>
            <Link href={o.href} className="gd-kompakt__link" aria-label={`${o.name} – Details`}>
              <span className="icon" aria-hidden data-icon="arrow_forward" />
            </Link>
          </div>
        ))}
        {geladen === null && !ladefehler && <div className="gd-kartenliste__hinweis" role="status">Orte werden geladen …</div>}
        {ladefehler && <div className="gd-leer" role="status">Die Orte konnten gerade nicht geladen werden. Bitte die Seite neu laden.</div>}
        {geladen !== null && !ladefehler && sichtbar.length === 0 && <div className="gd-leer">Keine Orte in diesem Bereich.</div>}
      </div>
      <div className="gd-karte-box">
        <div ref={kartenRef} className="gd-karte-map" />
        {fehler && (
          <div className="gd-karte-fehler" role="status">
            <span className="icon" aria-hidden data-icon="map" />
            Die Karte konnte gerade nicht geladen werden. Die Liste funktioniert weiterhin.
          </div>
        )}
        {bewegt && (
          <button
            type="button"
            className="gd-bereich-knopf"
            onClick={() => {
              const map = mapRef.current;
              if (!map) return;
              setBereich(map.getBounds());
              setBewegt(false);
              listeRef.current?.scrollTo({ top: 0 });
            }}
          >
            <span className="icon" aria-hidden data-icon="refresh" />In diesem Bereich suchen
          </button>
        )}
      </div>
    </div>
  );
}
