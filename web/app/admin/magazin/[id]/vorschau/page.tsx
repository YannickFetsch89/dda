// Admin-Bereich – Vorschau eines Magazin-Beitrags (Plan Admin-Dashboard 4.6, Cursor-Prüfung 2, Befund 4).
// Server-Komponente mit denselben Bausteinen wie /magazin/vorschau/[id] (MagazinArtikel). Statt des Vorschau-Schlüssels
// reicht die Admin-Sitzung; sie wird hier nur gelesen, nicht erneuert (adminSitzungLesen).
import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { Suspense } from "react";
import { MagazinArtikel } from "@/components/magazin-artikel";
import { istAdminBereich } from "@/lib/admin/bereich";
import { adminSitzungLesen } from "@/lib/admin/sitzung";
import { autorenLaden, beitragAus, eventsFuerIds, orteFuerSlugs } from "@/lib/magazin-daten";

export const metadata: Metadata = { title: "Magazin-Vorschau", robots: { index: false, follow: false } };

type Props = { params: Promise<{ id: string }> };

export default function AdminMagazinVorschau(props: Props) {
  return (
    <Suspense fallback={<p className="admin-unterzeile">Vorschau lädt …</p>}>
      <Inhalt {...props} />
    </Suspense>
  );
}

async function Inhalt({ params }: Props) {
  const { id } = await params;
  const kopf = await headers();
  const db = istAdminBereich(kopf) && /^[0-9a-f-]{36}$/i.test(id) ? await adminSitzungLesen(kopf) : null;
  if (!db) {
    return (
      <p className="admin-unterzeile">
        Sitzung abgelaufen oder nicht angemeldet. <Link href="/admin">Admin-Bereich neu laden</Link> und die Vorschau erneut öffnen.
      </p>
    );
  }
  const { data, error } = await db.rpc("admin_magazin_beitrag", { p_id: id.toLowerCase() });
  const b = !error && data ? beitragAus(data as Record<string, unknown>) : null;
  if (!b) return <p className="admin-fehler">Beitrag nicht gefunden.</p>;
  const [autoren, { events, heute }, orte] = await Promise.all([autorenLaden(), eventsFuerIds(b.event_ids), orteFuerSlugs(b.ort_slugs)]);
  return (
    <article className="mz-beitrag admin-vorschau">
      <p className="mz-hinweis" role="status">
        Vorschau im Admin-Bereich – {String((data as Record<string, unknown>).status)}. <Link href={`/admin/magazin/${b.id}`}>Zurück zum Bearbeiten</Link>
      </p>
      <MagazinArtikel b={b} autor={autoren.find((a) => a.slug === b.autor_slug) ?? null} events={events} orte={orte} heute={heute} ersatzHinweis />
    </article>
  );
}
