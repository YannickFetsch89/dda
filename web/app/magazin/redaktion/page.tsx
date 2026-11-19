// „Unsere Redaktion“ (Plan 2.3 Punkt 5): Redaktionskonzept, Pseudonyme, KI-Einsatz, Prüfung, Verantwortung, Korrekturen.
// Entwurf des Wortlauts – Freigabe durch den Auftraggeber in Schritt 5 (Plan Abschnitt 8).
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
    "Wer hinter dem Magazin von dies.das.düsseldorf steht, wie wir KI-Werkzeuge einsetzen, wie jeder Beitrag geprüft wird und wer redaktionell verantwortlich ist.",
  noindex: !MAGAZIN_VERLINKT,
});

export default async function RedaktionSeite() {
  const autoren = await autorenLaden();
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

        <h2 className="d">Redaktionelle Pseudonyme</h2>
        <p>
          Unsere Beiträge erscheinen unter redaktionellen Pseudonymen – je eines für einen Themenbereich. Hinter den
          Pseudonymen stehen keine einzelnen echten Personen mit eigener Biografie; sie stehen für ein Ressort und einen
          Ton. Wir geben ihnen deshalb keine Berufsbezeichnungen, Abschlüsse oder Lebensläufe. Die Profilbilder sind
          illustriert und KI-generiert und als solche gekennzeichnet.
        </p>
        {autoren.length > 0 && (
          <ul>
            {autoren.map((a) => (
              <li key={a.slug}>
                <Link href={autorPfad(a)}>{a.name}</Link> – {a.schwerpunkt}
              </li>
            ))}
          </ul>
        )}

        <h2 className="d">Wie Beiträge entstehen</h2>
        <p>
          Grundlage sind unsere eigenen Daten: Veranstaltungen aus den Programmen der Veranstalter und Orte aus unseren
          Guides. Daraus wählen wir nach festen Regeln aus, was in einen Beitrag kommt. KI-Werkzeuge schreiben daraus einen
          ersten Entwurf. Fakten wie Datum, Uhrzeit, Ort und Preis stehen nicht im Fließtext, sondern in den eingebetteten
          Karten – sie kommen live aus der Datenbank. Fällt ein Event aus, zeigt die Karte das sofort.
        </p>
        <p>
          Jeder Beitrag wird vor der Veröffentlichung von einem Menschen gelesen, korrigiert und freigegeben. Ohne diese
          Freigabe geht kein Beitrag online – auch technisch nicht.
        </p>

        <h2 className="d">Verantwortung</h2>
        <p>
          Redaktionell verantwortlich ist {VERANTWORTLICH}. Name und Anschrift stehen im <Link href="/impressum">Impressum</Link>.
        </p>

        <h2 className="d">Quellen, Bilder und Korrekturen</h2>
        <p>
          Unter jedem Beitrag nennen wir die Quellen. Aufmacherbilder sind eigene Fotos oder Symbolbilder; KI-generierte
          Symbolbilder kennzeichnen wir mit „Symbolbild (KI-generiert)“. Fotos aus Google Maps verwenden wir nicht.
        </p>
        <p>
          Wenn dir ein Fehler auffällt, schreib uns über die Adresse im <Link href="/impressum">Impressum</Link>. Sachliche
          Korrekturen kennzeichnen wir am Ende des Beitrags mit Datum.
        </p>
      </div>
    </div>
  );
}
