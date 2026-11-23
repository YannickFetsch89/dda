// Admin-Bereich – Event-Liste mit Suche und Filtern (Plan Admin-Dashboard 4.4). Liest mit dem Admin-Token; die
// Policy „Events lesen“ zeigt Admins auch abgelehnte Events.
import { LISTEN_FILTER, kategorieInDb, type ListenFilter } from "@/lib/admin/events";
import { adminAntwort, adminRoute } from "@/lib/admin/route";
import { heuteBerlin, plusTage } from "@/lib/datum";

const SEITE = 50;
const DATUM = /^\d{4}-\d{2}-\d{2}$/;
const LISTEN_SPALTEN =
  "id, slug, titel, datum, datum_bis, uhrzeit, ort, adresse, stadtteil, kategorie, unterkategorie, quelle_name, bild_url, " +
  "abgelehnt, abgesagt, nicht_empfehlen, tipp_des_tages, redaktion_felder, ort_id";

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const p = new URL(request.url).searchParams;
    const heute = heuteBerlin(new Date());
    const von = DATUM.test(p.get("von") ?? "") ? p.get("von")! : heute;
    const bis = DATUM.test(p.get("bis") ?? "") ? p.get("bis")! : plusTage(von, 6);
    const seite = Math.max(0, Math.min(200, Number(p.get("seite")) || 0));
    const filter = (p.get("filter") ?? "").split(",").filter((f): f is ListenFilter => (LISTEN_FILTER as readonly string[]).includes(f));

    let q = admin!.db
      .from("events")
      .select(LISTEN_SPALTEN, { count: "exact" })
      .lte("datum", bis)
      .or(`datum.gte.${von},datum_bis.gte.${von}`);
    const kategorie = p.get("kategorie") ? kategorieInDb(p.get("kategorie")!) : null;
    if (kategorie) q = q.eq("kategorie", kategorie);
    const stadtteil = p.get("stadtteil")?.trim();
    if (stadtteil) q = q.eq("stadtteil", stadtteil);
    const quelle = p.get("quelle")?.trim();
    if (quelle) q = q.ilike("quelle_name", `%${quelle.replace(/[%_,()]/g, "")}%`);
    const suche = p.get("q")?.trim().replace(/[%_,()*]/g, " ").slice(0, 80);
    if (suche) q = q.or(`titel.ilike.*${suche}*,ort.ilike.*${suche}*`);
    // Ohne Filter „abgelehnt“ nur sichtbare Events
    q = q.eq("abgelehnt", filter.includes("abgelehnt"));
    if (filter.includes("abgesagt")) q = q.eq("abgesagt", true);
    if (filter.includes("nicht_empfehlen")) q = q.eq("nicht_empfehlen", true);
    if (filter.includes("ohne_bild")) q = q.is("bild_url", null);
    if (filter.includes("ohne_stadtteil")) q = q.is("stadtteil", null);
    if (filter.includes("ohne_adresse")) q = q.is("adresse", null);
    if (filter.includes("ohne_ort_id")) q = q.is("ort_id", null);
    if (filter.includes("redaktion")) q = q.neq("redaktion_felder", "{}");

    const { data, count, error } = await q
      .order("datum")
      .order("uhrzeit", { nullsFirst: true })
      .order("titel")
      .range(seite * SEITE, seite * SEITE + SEITE - 1);
    if (error) return adminAntwort(500, { fehler: error.message, code: "db" }, setCookies);
    return adminAntwort(200, { von, bis, seite, proSeite: SEITE, gesamt: count ?? 0, events: data ?? [] }, setCookies);
  });
}
