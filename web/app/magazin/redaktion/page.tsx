// „Unsere Redaktion“ (Plan 2.3 Punkt 5, überarbeitet 20.11.2026 nach rechtlicher Prüfung): Einleitung, Autoren mit
// Themenbereichen, „So arbeitet unsere Redaktion“ (Wortlaut vom Auftraggeber), Quellen/Bilder/Korrekturen kurz.
// Pseudonyme bleiben offen benannt, KI-Unterstützung und menschliche Freigabe dezent statt als Belehrung.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { jsonLdText } from "@/lib/json-ld";
import { autorPfad, VERANTWORTLICH } from "@/lib/magazin";
import { autorenLaden } from "@/lib/magazin-daten";
import { redaktionJsonLd } from "@/lib/magazin-json-ld";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";
import { seitenMetadaten } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/magazin/redaktion",
  titel: "Unsere Redaktion – so entsteht das Magazin",
  beschreibung:
    "Die Redaktion hinter dem Magazin von dies.das.düsseldorf: Themenbereiche, Autoren, wie Beiträge entstehen und geprüft werden und wer redaktionell verantwortlich ist.",
  noindex: !MAGAZIN_VERLINKT,
});

export default async function RedaktionSeite() {
  const autoren = [...(await autorenLaden())].sort((a, b) => a.name.localeCompare(b.name, "de"));
  return (
    <div className="container sektion mz-redaktion">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(redaktionJsonLd(SITE_URL)) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <Link href="/magazin">Magazin</Link>
        <span>/</span>
        <span aria-current="page">Unsere Redaktion</span>
      </nav>
      <h1 className="d">Unsere Redaktion</h1>
      <div className="mz-text">
        <p>
          dies.das.düsseldorf sammelt jeden Tag Events, Orte und Termine aus Düsseldorf, Neuss und Ratingen. Im Magazin
          ordnen wir diese Daten ein: Was lohnt sich diese Woche, welcher Weihnachtsmarkt passt zu wem, wo man an welchem
          Abend ausgeht.
        </p>

        {autoren.length > 0 && (
          <>
            <h2 className="d">Unsere Autoren</h2>
            <ul className="mz-autorenliste">
              {autoren.map((a) => (
                <li key={a.slug}>
                  <Link href={autorPfad(a)} className="mz-autorenliste__link">
                    {a.bild && (
                      // eslint-disable-next-line @next/next/no-img-element -- statisches Profilbild aus public/
                      <img src={a.bild} alt="" width={56} height={56} loading="lazy" />
                    )}
                    <span>
                      <strong>{a.name}</strong>
                      <span className="mz-autorenliste__fach">{a.schwerpunkt}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}

        <h2 className="d">So arbeitet unsere Redaktion</h2>
        <p>Unser Magazin berichtet über Veranstaltungen, Gastronomie, Kultur und das Stadtleben in Düsseldorf.</p>
        <p>
          Unsere Beiträge entstehen auf Grundlage eigener Veranstaltungsdaten, redaktioneller Recherche und teilweise
          mithilfe KI-gestützter Werkzeuge. Alle Inhalte werden vor der Veröffentlichung auf Fakten, Quellen und Relevanz
          geprüft und redaktionell freigegeben.
        </p>
        <p>
          Die Autorennamen stehen für unterschiedliche Themenbereiche und werden als redaktionelle Pseudonyme verwendet.
          Die redaktionelle Verantwortung trägt {VERANTWORTLICH}. Weitere Informationen findest du im{" "}
          <Link href="/impressum">Impressum</Link>.
        </p>

        <h2 className="d">Quellen, Bilder und Korrekturen</h2>
        <p>
          Unter jedem Beitrag nennen wir die Quellen. Termine, Uhrzeiten und Preise kommen direkt aus unserer
          Veranstaltungsdatenbank – fällt ein Event aus, zeigt der Beitrag das sofort. Aufmacherbilder sind eigene Fotos
          oder Symbolbilder; KI-generierte Symbolbilder sind als solche gekennzeichnet.
        </p>
        <p>
          Fällt dir ein Fehler auf, schreib uns über die Adresse im <Link href="/impressum">Impressum</Link>. Sachliche
          Korrekturen vermerken wir am Ende des Beitrags mit Datum.
        </p>
      </div>
    </div>
  );
}
