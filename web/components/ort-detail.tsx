// Gemeinsame Bausteine der Guide-Detailseiten (Restaurants & Cafés, Kneipen & Bars):
// Info-Zeile, Öffnungszeiten (zur Anfragezeit, eigene Suspense-Grenze), Domain-Anzeige.
import { connection } from "next/server";
import { Icon } from "./karten";

const WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];
const ZEITRAUM = /(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})/g;

/**
 * Google-Öffnungszeiten ("Montag: 12:00–22:00 Uhr | Dienstag: …") → Zeilen, dazu die von heute (Berlin).
 * Reicht ein Zeitraum des Vortags über Mitternacht ("Freitag: 18:00–02:00") und ist es jetzt davor,
 * gilt das Lokal als noch geöffnet – sonst stünde samstags um 01:00 oft "Geschlossen" da.
 */
export function oeffnungszeiten(text: string | null, jetzt: Date) {
  const tage = (text ?? "").split("|").map((z) => z.trim()).filter(Boolean).map((z) => {
    const i = z.indexOf(":");
    return i > 0 ? { tag: z.slice(0, i).trim(), zeit: z.slice(i + 1).trim() } : { tag: "", zeit: z };
  });
  const teile = Object.fromEntries(
    new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", weekday: "long", hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
      .formatToParts(jetzt).map((p) => [p.type, p.value]),
  );
  const heuteName = teile.weekday;
  const minuten = Number(teile.hour) * 60 + Number(teile.minute);
  const vortag = WOCHENTAGE[(WOCHENTAGE.indexOf(heuteName) + 6) % 7];

  let nochBis: string | null = null;
  for (const m of (tage.find((t) => t.tag === vortag)?.zeit ?? "").matchAll(ZEITRAUM)) {
    const start = Number(m[1]) * 60 + Number(m[2]);
    const ende = Number(m[3]) * 60 + Number(m[4]);
    if (ende < start && minuten < ende) nochBis = `${m[3].padStart(2, "0")}:${m[4]}`;
  }
  return { heute: tage.find((t) => t.tag === heuteName)?.zeit ?? null, nochBis, tage };
}

export function InfoZeile({ icon, l1, l2, children }: { icon: string; l1: React.ReactNode; l2?: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="gd-info__zeile">
      <Icon name={icon} />
      <div>
        <span>{l1}</span>
        {l2 && <span className="muted">{l2}</span>}
        {children}
      </div>
    </div>
  );
}

/** Öffnungszeiten hängen vom heutigen Wochentag ab – daher erst zur Anfragezeit (eigene Suspense-Grenze). */
export async function Oeffnungszeiten({ text }: { text: string }) {
  await connection();
  const oz = oeffnungszeiten(text, new Date());
  const heute = oz.heute ? `Heute: ${oz.heute}` : "Öffnungszeiten";
  return (
    <InfoZeile icon="schedule" l1={oz.nochBis ? `Noch geöffnet bis ${oz.nochBis} Uhr` : heute} l2={oz.nochBis ? heute : undefined}>
      <details className="gd-oz">
        <summary>Alle Öffnungszeiten</summary>
        <dl>
          {oz.tage.map((t) => (
            <div key={t.tag + t.zeit}><dt>{t.tag}</dt><dd>{t.zeit}</dd></div>
          ))}
        </dl>
      </details>
    </InfoZeile>
  );
}

export function domain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}
