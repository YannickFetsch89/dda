// Event-Darstellungen: Standard-Card, Rang-Card, Kompakt-Card, Listenzeilen
import Link from "next/link";
import { BildImg, HerzButton } from "./client";
import { eventBildUrl } from "@/lib/bilder";
import { katStil, kategorie } from "@/lib/kategorien";
import { metaZeile } from "@/lib/datum";
import { stadtteilName } from "@/lib/stadtteile";
import { symbolbild } from "@/lib/symbolbild";
import { istOnline } from "@/lib/ableitungen";
import type { DddEvent } from "@/lib/typen";

import { anzeigeTitel, zeitKurz } from "@/lib/termine";

// Kanonischer Event-Pfad liegt in lib/pfade.ts (auch für Client-Komponenten und proxy.ts)
import { eventPfad } from "@/lib/pfade";
export { eventPfad };

export function Icon({ name, className }: { name: string; className?: string }) {
  return (
    // Name als Attribut, nicht als Text: CSS zeigt ihn über ::before als Ligatur an. So landen „search“,
    // „arrow_forward“ & Co. nicht im Textauszug von Crawlern und KI-Systemen (SEO-/GEO-Plan, Maßnahme 10)
    <span className={className ? `icon ${className}` : "icon"} aria-hidden data-icon={name} />
  );
}

export function Bild({
  e,
  className = "",
  eager = false,
  vollstaendig = false,
  alt = "",
  symbolAlt,
  children,
}: {
  e: DddEvent;
  className?: string;
  eager?: boolean;
  vollstaendig?: boolean;
  /** Nur fürs Hero der Eventseite; in Listen leer lassen (der Titel steht im selben Link als Text) */
  alt?: string;
  symbolAlt?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className={`bild ${e.abgesagt ? "bild--abgesagt" : ""} ${className}`} style={katStil(e.kategorie)}>
      <BildImg src={eventBildUrl(e)} ersatz={symbolbild(e)} alt={alt} symbolAlt={symbolAlt} icon={kategorie(e.kategorie).icon} eager={eager} vollstaendig={vollstaendig} />
      {e.abgesagt && <AbgesagtTag className="bild__abgesagt" />}
      {!e.abgesagt && istOnline(e) && <OnlineTag className="bild__online" />}
      {children}
    </div>
  );
}

/** Rotes Schild für abgesagte Events */
export function AbgesagtTag({ className = "" }: { className?: string }) {
  return <span className={`abgesagt-tag ${className}`}>Abgesagt</span>;
}

export function OnlineTag({ className = "" }: { className?: string }) {
  return <span className={`online-tag ${className}`}><Icon name="videocam" />Online</span>;
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
          <Link href={eventPfad(e)}>{anzeigeTitel(e.titel, e.ort)}</Link>
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
        <span className="icon" aria-hidden data-icon={k.icon} />
      </span>
      <div className="kompakt__text">
        <span className="meta">{metaZeile(e, heute)}</span>
        <h3 className="kompakt__titel">
          <Link href={eventPfad(e)}>{anzeigeTitel(e.titel, e.ort)}</Link>
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
      <span className="zeile__zeit">{zeit ?? zeitKurz(e) ?? "–"}</span>
      <span className="punkt" style={katStil(e.kategorie)} aria-hidden />
      <div className="zeile__text">
        <span className="zeile__titel">
          {e.abgesagt && <AbgesagtTag />}
          <Link href={eventPfad(e)}>{anzeigeTitel(e.titel, e.ort)}</Link>
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
          <Link href={eventPfad(e)}>{anzeigeTitel(e.titel, e.ort)}</Link>
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
          <Link href={eventPfad(e)}>{anzeigeTitel(e.titel, e.ort)}</Link>
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
