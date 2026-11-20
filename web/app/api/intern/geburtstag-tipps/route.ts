// Interne Route für den Versandjob der Geburtstagsmail (Plan docs/plan-geburtstagsmail-2026-11-20.md, G2).
// POST { nutzer: [id, …] } (höchstens 200) mit Header x-geburtstag-schluessel = GEBURTSTAG_JOB_SCHLUESSEL
// → { datum, allgemein: [Tipp], tipps: { <id>: [Tipp] } }, je höchstens drei. Keine Mailadressen, keine Interessen,
// keine Begründungen in der Antwort. Ohne/mit falschem Schlüssel oder ohne Schalter → 404 (verrät die Route nicht).
// Sensibel-Menge oder Profile nicht lesbar → 503; der Job schickt dann die Mail ohne Tipp-Block. Immer no-store.
import type { NextRequest } from "next/server";
import { eventPoolLaden } from "@/lib/daten";
import { kontoDienstClient } from "@/lib/konto/clients";
import { allgemeineTipps, tippAusgabe, tippsFuerNutzer, TIPPS_MAX } from "@/lib/konto/geburtstag-tipps";
import { kontenAktiv } from "@/lib/konto/konfig";
import { eingabeAusProfil, sensibelMenge, type KontoMerkliste } from "@/lib/konto/mein-bereich";
import { eventsFuerIds } from "@/lib/konto/merkliste-events";
import { uuidGueltig } from "@/lib/konto/pruefungen";
import { schluesselOk } from "@/lib/magazin-auswahl";
import type { DddEvent } from "@/lib/typen";

const KOPF = { "Cache-Control": "no-store" };
const NUTZER_MAX = 200;
// Die Merkliste fasst MERKLISTE_MAX (500) Einträge; mehr Zeilen wären ein Zeichen für eine unvollständige Antwort
const MERK_ABFRAGE_MAX = 1000;
const nichtDa = () => new Response("Nicht gefunden", { status: 404, headers: { ...KOPF, "Content-Type": "text/plain; charset=utf-8" } });
const fehler = (status: number, text: string) => Response.json({ fehler: text }, { status, headers: KOPF });

export async function GET() {
  return nichtDa();
}

export async function POST(req: NextRequest) {
  if (!kontenAktiv() || !schluesselOk(req.headers.get("x-geburtstag-schluessel"), process.env.GEBURTSTAG_JOB_SCHLUESSEL)) {
    return nichtDa();
  }
  let eingabe: { nutzer?: unknown };
  try {
    eingabe = await req.json();
  } catch {
    return fehler(400, "Ungültiges JSON");
  }
  const roh = Array.isArray(eingabe?.nutzer) ? eingabe.nutzer : [];
  if (roh.length > NUTZER_MAX) return fehler(400, `Höchstens ${NUTZER_MAX} Nutzer je Anfrage`);
  const nutzer = [...new Set(roh.filter((x): x is string => typeof x === "string" && uuidGueltig(x)))];

  const dienst = kontoDienstClient();
  const sensibel = await sensibelMenge();
  if (!dienst || !sensibel) return fehler(503, "Daten nicht verfügbar");

  try {
    // Nur echte Events: Bei einem Ladefehler liefert eventPoolLaden Beispieldaten mit heutigem Datum. Die darf die
    // Startseite zeigen, eine Mail aber nie als Tipp verschicken (Cursor-Befund, hoch). Der Job schickt dann ohne Tipps.
    const pool = await eventPoolLaden();
    if (pool.quelle !== "supabase") return fehler(503, "Daten nicht verfügbar");
    // Grundlage für die allgemeinen Tipps: dieselbe Eingabe ohne Interessen (Pool, heute, Stufen)
    const basis = await eingabeAusProfil({ personalisierung: false, praeferenzen: {} }, null, sensibel);
    const allgemein = allgemeineTipps(basis.events, basis.stufen, basis.heute, sensibel);
    const tipps: Record<string, ReturnType<typeof tippAusgabe>[]> = {};

    if (nutzer.length) {
      const profile = await dienst.from("profiles").select("id, personalisierung, praeferenzen").in("id", nutzer);
      if (profile.error) return fehler(503, "Daten nicht verfügbar");
      // Merkliste je Person einzeln (höchstens MERKLISTE_MAX Zeilen): Eine Sammelabfrage könnte Supabase still kürzen,
      // dann fiele ein gemerktes Event nicht heraus (Cursor-Befund, gering). Volle Antwort → 503 statt halber Tipps.
      const zeilenJe = new Map<string, { event_id: string; gemerkt_am: string }[]>();
      for (const id of (profile.data ?? []).map((p) => p.id as string)) {
        const merk = await dienst.from("merkliste").select("event_id, gemerkt_am").eq("nutzer_id", id).limit(MERK_ABFRAGE_MAX);
        if (merk.error || (merk.data ?? []).length >= MERK_ABFRAGE_MAX) return fehler(503, "Daten nicht verfügbar");
        zeilenJe.set(id, (merk.data ?? []).map((z) => ({ event_id: z.event_id as string, gemerkt_am: z.gemerkt_am as string })));
      }
      // Events der Merklisten nur für Personen mit Einwilligung (a) laden – nur dort fließen sie in Punkte ein
      const mitA = new Set((profile.data ?? []).filter((p) => p.personalisierung).map((p) => p.id as string));
      const ids = [...new Set([...zeilenJe].filter(([id]) => mitA.has(id)).flatMap(([, z]) => z.map((x) => x.event_id)))];
      let geladen: DddEvent[] = [];
      let eventsFehler = false;
      try {
        geladen = (await eventsFuerIds(ids)).events;
      } catch {
        eventsFehler = true;
      }
      const eventJe = new Map(geladen.map((e) => [e.id, e]));

      for (const p of profile.data ?? []) {
        const id = p.id as string;
        const zeilen = zeilenJe.get(id) ?? [];
        const merkliste: KontoMerkliste = {
          zeilen,
          events: zeilen.map((z) => eventJe.get(z.event_id)).filter((e): e is DddEvent => !!e),
          heute: basis.heute,
          eventsFehler,
        };
        const e = await eingabeAusProfil(
          { personalisierung: !!p.personalisierung, praeferenzen: (p.praeferenzen ?? {}) as Record<string, unknown> },
          merkliste,
          sensibel,
        );
        const gemerkt = new Set(zeilen.map((z) => z.event_id));
        tipps[id] = tippsFuerNutzer(e, gemerkt, allgemein).map(tippAusgabe);
      }
    }

    return Response.json({ datum: basis.heute, allgemein: allgemein.slice(0, TIPPS_MAX).map(tippAusgabe), tipps }, { headers: KOPF });
  } catch (err) {
    console.error(`Geburtstags-Tipps: ${err instanceof Error ? err.name : "unbekannt"}`);
    return fehler(503, "Daten nicht verfügbar");
  }
}
