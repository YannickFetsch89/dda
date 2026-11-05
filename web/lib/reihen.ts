// Reihen (wiederkehrende Events): dauerhafte Seite /reihe/<slug> mit nächstem und allen kommenden Terminen.
// Die Zuordnung Event → Reihe macht die Pipeline (pipeline/reihen_zuordnen.py).
import { cacheLife } from "next/cache";
import { heuteBerlin } from "./datum";
import { mitSpalten, normalisieren, supabaseClient, type Zeile } from "./daten";
import { buendeln } from "./termine";
import type { DddEvent, KategorieSlug } from "./typen";
import { kategorieAusDb } from "./kategorien";

export interface Reihe {
  id: string;
  slug: string;
  titel: string;
  ort: string;
  kategorie: KategorieSlug;
}

export interface ReiheDaten {
  reihe: Reihe;
  heute: string;
  /** Kommende (und laufende) Termine, mehrere Uhrzeiten eines Tages gebündelt */
  kommende: DddEvent[];
  /** Letzter vergangener Termin – für Reihen, die gerade keine kommenden Termine haben */
  letzter: DddEvent | null;
}

export async function reiheLaden(slug: string): Promise<ReiheDaten | null> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 600, expire: 3600 });

  const client = supabaseClient();
  if (!client) return null;
  try {
    const { data: r, error } = await client.from("reihen").select("id, slug, titel, ort, kategorie").eq("slug", slug).maybeSingle();
    if (error || !r) return null;
    const heute = heuteBerlin(new Date());
    const kommend = await mitSpalten<Zeile[]>((spalten) =>
      client
        .from("events")
        .select(spalten)
        .eq("reihe_id", r.id)
        .eq("abgelehnt", false)
        .or(`datum.gte.${heute},datum_bis.gte.${heute}`)
        .order("datum", { ascending: true })
        .order("uhrzeit", { ascending: true })
        .limit(500)
        .then((x) => x as unknown as { data: Zeile[] | null; error: { message: string } | null }),
    );
    const kommende = buendeln((kommend.data ?? []).map(normalisieren));
    let letzter: DddEvent | null = null;
    if (!kommende.length) {
      const alt = await mitSpalten<Zeile[]>((spalten) =>
        client
          .from("events")
          .select(spalten)
          .eq("reihe_id", r.id)
          .eq("abgelehnt", false)
          .lt("datum", heute)
          .order("datum", { ascending: false })
          .limit(1)
          .then((x) => x as unknown as { data: Zeile[] | null; error: { message: string } | null }),
      );
      letzter = alt.data?.[0] ? normalisieren(alt.data[0]) : null;
    }
    return {
      reihe: { id: String(r.id), slug: String(r.slug), titel: String(r.titel), ort: String(r.ort), kategorie: kategorieAusDb(r.kategorie as string | null) },
      heute,
      kommende,
      letzter,
    };
  } catch (err) {
    console.error(`Reihe ${slug} konnte nicht geladen werden: ${err instanceof Error ? err.message : err}`);
    return null;
  }
}
