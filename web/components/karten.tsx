// Event-Darstellungen: Standard-Card, Rang-Card, Kompakt-Card, Listenzeilen
import Link from "next/link";
import { BildImg, HerzButton } from "./client";
import { katStil, kategorie } from "@/lib/kategorien";
import { metaZeile } from "@/lib/datum";
import { stadtteilName } from "@/lib/stadtteile";
import { symbolbild } from "@/lib/symbolbild";
import type { DddEvent } from "@/lib/typen";

export function eventPfad(e: DddEvent) {
  return `/event/${encodeURIComponent(e.id)}`;
}

export function Icon({ name, className }: { name: string; className?: string }) {
  return (
    <span className={className ? `icon ${className}` : "icon"} aria-hidden>
      {name}
    </span>
  );
}

export function Bild({
  e,
  className = "",
  eager = false,
  vollstaendig = false,
  children,
}: {
  e: DddEvent;
  className?: string;
  eager?: boolean;
  vollstaendig?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className={`bild ${className}`} style={katStil(e.kategorie)}>
      <BildImg src={e.bild_url} ersatz={symbolbild(e)} alt="" icon={kategorie(e.kategorie).icon} eager={eager} vollstaendig={vollstaendig} />
      {children}
    </div>
  );
}

export function KatBadge({ slug, variante = "" }: { slug: string; variante?: string }) {
  const k = kategorie(slug);
  return (
    <span className={`badge ${variante}`} style={katStil(slug)}>
      <Icon name={k.icon} />
      {k.name}
    </span>
  );
}

export function KatLabel({ slug }: { slug: string }) {
  const k = kategorie(slug);
  return (
    <span className="katlabel" style={katStil(slug)}>
      <Icon name={k.icon} />
      {k.name}
    </span>
  );
}

export function preisText(e: DddEvent) {
  return e.preis ?? "";
}

type Variante = "standard" | "reihe" | "grid" | "rang";

export function EventKarte({ e, heute, variante = "standard", rang, gross = false }: { e: DddEvent; heute: string; variante?: Variante; rang?: number; gross?: boolean }) {
  const klassen = ["karte", variante !== "standard" && `karte--${variante}`, gross && "karte--gross"].filter(Boolean).join(" ");
  return (
    <article className={klassen} role="listitem">
      <Bild e={e}>
        {variante !== "reihe" && <KatBadge slug={e.kategorie} />}
        {rang !== undefined && <span className="rang">{rang}</span>}
      </Bild>
      <HerzButton id={e.id} titel={e.titel} />
      <div className="karte__text">
        <span className="meta">{metaZeile(e, heute)}</span>
        <h3 className="karte__titel">
          <Link href={eventPfad(e)}>{e.titel}</Link>
        </h3>
        <span className="karte__fuss">
          <span>{e.ort}</span>
          <span className="preis">{preisText(e)}</span>
        </span>
      </div>
    </article>
  );
}

export function KompaktKarte({ e, heute }: { e: DddEvent; heute: string }) {
  const k = kategorie(e.kategorie);
  return (
    <article className="kompakt" role="listitem">
      <Bild e={e} />
      <span className="kompakt__icon" style={katStil(e.kategorie)} aria-hidden>
        <span className="icon">{k.icon}</span>
      </span>
      <div className="kompakt__text">
        <span className="meta">{metaZeile(e, heute)}</span>
        <h3 className="kompakt__titel">
          <Link href={eventPfad(e)}>{e.titel}</Link>
        </h3>
        <span className="kompakt__ort">
          {e.ort}
          {e.preis ? ` · ${e.preis}` : ""}
        </span>
      </div>
    </article>
  );
}

/** Listenzeile mit Zeit, Kategorie-Punkt, Titel, Ort und Preis */
export function ListenZeile({ e, mitKategorie = false, zeit }: { e: DddEvent; mitKategorie?: boolean; zeit?: string }) {
  return (
    <div className="zeile">
      <span className="zeile__zeit">{zeit ?? e.uhrzeit ?? "–"}</span>
      <span className="punkt" style={katStil(e.kategorie)} aria-hidden />
      <div className="zeile__text">
        <span className="zeile__titel">
          <Link href={eventPfad(e)}>{e.titel}</Link>
        </span>
        <span className="zeile__sub">
          {e.ort}
          {mitKategorie ? ` · ${kategorie(e.kategorie).name}` : ""}
        </span>
      </div>
      {e.preis && <span className="preis">{e.preis}</span>}
    </div>
  );
}

/** Zeile mit Thumbnail ("Gerade neu") */
export function ThumbZeile({ e, heute }: { e: DddEvent; heute: string }) {
  return (
    <div className="zeile">
      <Bild e={e} className="zeile__thumb" />
      <div className="zeile__text">
        <span className="zeile__titel">
          <Link href={eventPfad(e)}>{e.titel}</Link>
        </span>
        <span className="zeile__sub">
          {metaZeile(e, heute)} · {e.ort}
        </span>
      </div>
    </div>
  );
}

export function GratisZeile({ e, heute }: { e: DddEvent; heute: string }) {
  return (
    <article className="gratis-zeile" role="listitem">
      <Bild e={e} />
      <div className="gratis-zeile__text">
        <KatLabel slug={e.kategorie} />
        <h3 className="gratis-zeile__titel">
          <Link href={eventPfad(e)}>{e.titel}</Link>
        </h3>
        <span className="zeile__sub">
          {metaZeile(e, heute)} · {e.stadtteil ? stadtteilName(e.stadtteil) : e.ort}
        </span>
      </div>
      <span className="badge badge--gratis">Gratis</span>
    </article>
  );
}

export function Leer({ titel, children }: { titel: string; children?: React.ReactNode }) {
  return (
    <div className="leer">
      <span className="d">{titel}</span>
      {children}
    </div>
  );
}

export function SkeletonKarten({ anzahl = 4, hoehe = 260 }: { anzahl?: number; hoehe?: number }) {
  return (
    <div className="raster" aria-busy="true" aria-label="Lädt …">
      {Array.from({ length: anzahl }, (_, i) => (
        <div key={i} className="skeleton" style={{ height: hoehe }} />
      ))}
    </div>
  );
}
