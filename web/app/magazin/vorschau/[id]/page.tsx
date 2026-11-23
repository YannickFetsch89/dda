// Entwurfs-Vorschau (Plan docs/plan-redaktion-2026-11-19.md, 5.3). Zugang entscheidet proxy.ts (UUID, Schlüssel ?s=,
// SHA-256 = vorschau_hash, Status entwurf/in_pruefung) – ohne gültigen Schlüssel echte 404, bevor etwas rendert.
// Hier die zweite Sicherung: Hash erneut prüfen; bei Fehlschlag wird nichts vom Entwurf gerendert.
// Kein "use cache", noindex/nofollow; Cache-Control und Referrer-Policy setzt proxy.ts.
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { MagazinArtikel } from "@/components/magazin-artikel";
import { autorenLaden, eventsFuerIds, orteFuerSlugs, vorschauLaden } from "@/lib/magazin-daten";
import { gleichZeitkonstant, sha256Hex } from "@/lib/pfad-pruefung";

export const metadata: Metadata = { title: "Vorschau", robots: { index: false, follow: false } };

type Props = { params: Promise<{ id: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };

export default function VorschauSeite(props: Props) {
  return (
    <Suspense fallback={<div className="container sektion">Vorschau lädt …</div>}>
      <VorschauInhalt {...props} />
    </Suspense>
  );
}

function PruefListe({ pruefung }: { pruefung: Record<string, unknown> }) {
  const ergebnis = typeof pruefung.ergebnis === "string" ? pruefung.ergebnis : "ungeprüft";
  const punkte = Array.isArray(pruefung.punkte) ? (pruefung.punkte as unknown[]).map(String) : [];
  return (
    <aside className={ergebnis === "gruen" ? "mz-pruefung mz-pruefung--gruen" : "mz-pruefung mz-pruefung--rot"}>
      <strong>Automatische Prüfung: {ergebnis}</strong>
      {punkte.length > 0 && <ul>{punkte.map((p, i) => <li key={i}>{p}</li>)}</ul>}
    </aside>
  );
}

async function VorschauInhalt({ params, searchParams }: Props) {
  const { id } = await params;
  const s = (await searchParams).s;
  const schluessel = typeof s === "string" ? s : null;
  const v = /^[0-9a-f-]{36}$/i.test(id) ? await vorschauLaden(id.toLowerCase()) : null;
  const ok = !!v && !!schluessel && !!v.hash && gleichZeitkonstant(await sha256Hex(schluessel), v.hash);
  if (!v || !ok) {
    return (
      <div className="container sektion">
        <h1 className="d">Vorschau nicht verfügbar</h1>
        <p>Der Link ist ungültig oder der Beitrag ist schon veröffentlicht.</p>
        <Link href="/magazin">Zum Magazin</Link>
      </div>
    );
  }
  const b = v.beitrag;
  const [autoren, { events, heute }, orte] = await Promise.all([autorenLaden(), eventsFuerIds(b.event_ids), orteFuerSlugs(b.ort_slugs)]);
  const autor = autoren.find((a) => a.slug === b.autor_slug) ?? null;
  return (
    <article className="container sektion mz-beitrag">
      <p className="mz-hinweis" role="status">Entwurfs-Vorschau – nicht öffentlich.</p>
      <PruefListe pruefung={v.pruefung} />
      <MagazinArtikel b={b} autor={autor} events={events} orte={orte} heute={heute} ersatzHinweis />
    </article>
  );
}
