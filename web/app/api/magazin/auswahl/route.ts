// Interne Auswahl-Route für die Magazin-Pipeline (Plan docs/plan-redaktion-2026-11-19.md, T11).
// POST { rubrik, von, bis } mit Header x-magazin-schluessel → Kandidaten mit Event-IDs, Highlight bzw. Top.
// Ohne/mit falschem Schlüssel oder ohne gesetzte Umgebungsvariable → 404 (nie 500). Zeitraum passt nicht → 400.
// Datenbankfehler → 503 (der Job bricht dann ab: kein Entwurf, kein Modellaufruf). Immer no-store.
import type { NextRequest } from "next/server";
import { magazinPoolLaden } from "@/lib/daten";
import { auswahlRechnen, schluesselOk, zeitraumPassend } from "@/lib/magazin-auswahl";

const KOPF = { "Cache-Control": "no-store" };
const nichtDa = () => new Response("Nicht gefunden", { status: 404, headers: { ...KOPF, "Content-Type": "text/plain; charset=utf-8" } });

export async function GET() {
  return nichtDa();
}

export async function POST(req: NextRequest) {
  if (!schluesselOk(req.headers.get("x-magazin-schluessel"))) return nichtDa();
  let eingabe: { rubrik?: unknown; von?: unknown; bis?: unknown };
  try {
    eingabe = await req.json();
  } catch {
    return Response.json({ fehler: "Ungültiges JSON" }, { status: 400, headers: KOPF });
  }
  const rubrik = String(eingabe.rubrik ?? "");
  const von = String(eingabe.von ?? "");
  const bis = String(eingabe.bis ?? "");
  if (!zeitraumPassend(rubrik, von, bis)) {
    return Response.json({ fehler: "Zeitraum passt nicht zur Rubrik (Wochenvorschau Mo–So, Monats-Tipps ganzer Monat)" }, { status: 400, headers: KOPF });
  }
  try {
    const pool = await magazinPoolLaden(von, bis);
    return Response.json(auswahlRechnen(pool, rubrik, von, bis), { headers: KOPF });
  } catch (err) {
    console.error(`Magazin-Auswahl ${rubrik} ${von}–${bis}: ${err instanceof Error ? err.message : err}`);
    return Response.json({ fehler: "Daten nicht verfügbar" }, { status: 503, headers: KOPF });
  }
}
