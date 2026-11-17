// Nutzungsbedingungen für Nutzerkonten (Plan Nutzerkonten E14, Schritt 6). Wortlaut aus
// docs/nutzungsbedingungen-entwurf-2026-11-16.md, vom Anwalt als „so umsetzbar“ bestätigt (Mitteilung des
// Auftraggebers vom 17.11.2026); § 3 Abs. 2 (E16) geht zusätzlich in die schriftliche Freigabe.
// Sie-Form wie Datenschutzerklärung und Impressum. Ohne KONTEN_AKTIV gibt es die Seite nicht (404).
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { kontenAktiv, TEXTVERSIONEN } from "@/lib/konto/konfig";

/** Auf den Monat setzen, in dem KONTEN_AKTIV eingeschaltet wird (wie STAND_MIT_KONTEN in datenschutz/page.tsx). */
const STAND = "November 2026";

export const metadata: Metadata = {
  title: "Nutzungsbedingungen",
  description: "Nutzungsbedingungen für Nutzerkonten auf dies.das.düsseldorf.",
};

export default function NutzungsbedingungenSeite() {
  if (!kontenAktiv()) notFound();
  return (
    <div className="container sektion rechtliches">
      <h1 className="d">Nutzungsbedingungen</h1>
      <p className="klein">
        für Nutzerkonten · Stand: {STAND} · Version: {TEXTVERSIONEN.nutzungsbedingungen}
      </p>

      <h2>§ 1 Geltungsbereich und Anbieter</h2>
      <p>
        (1) Diese Nutzungsbedingungen gelten für die Nutzung von Nutzerkonten auf der Website diesdas.events
        („dies.das.düsseldorf“) und, sobald verfügbar, in der zugehörigen App.
      </p>
      <p>
        (2) Anbieter ist die Rocktician e.&thinsp;K., Inhaber Yannick Fetsch, Erkrather Str. 401, 40231 Düsseldorf,
        eingetragen im Handelsregister des Amtsgerichts Mannheim unter HRA 707668, E-Mail:{" "}
        <a href="mailto:moin@rocktician.com">moin@rocktician.com</a> (im Folgenden „wir“).
      </p>
      <p>(3) Die Website lässt sich auch ohne Konto nutzen. Für die Nutzung ohne Konto gelten diese Bedingungen nicht.</p>
      <p>(4) Abweichende Bedingungen der Nutzerinnen und Nutzer gelten nicht.</p>

      <h2>§ 2 Leistungen</h2>
      <p>
        (1) dies.das.düsseldorf ist ein kostenloser Veranstaltungskalender für Düsseldorf und Umgebung. Mit einem Konto
        können Sie insbesondere:
      </p>
      <ul>
        <li>
          Events merken und Ihre Merkliste auf mehreren Geräten nutzen. Ausgenommen sind Events, aus deren Merkung sich
          besonders schützenswerte Angaben ableiten lassen (etwa zu Gesundheit, Religion oder sexueller Orientierung).
          Diese speichern wir nur mit Ihrer ausdrücklichen Einwilligung in Ihrem Konto, sonst nur auf dem Gerät, auf dem
          Sie sie gemerkt haben (Einzelheiten in der Datenschutzerklärung),
        </li>
        <li>freiwillig Interessen angeben und, wenn Sie einwilligen, persönliche Event-Vorschläge erhalten,</li>
        <li>wenn Sie einwilligen, zum Geburtstag eine Mail mit Glückwünschen und Event-Tipps erhalten,</li>
        <li>Ihre Einstellungen und Einwilligungen verwalten, Ihre Daten herunterladen und Ihr Konto löschen.</li>
      </ul>
      <p>
        (2) Das Konto ist kostenlos. Ein Anspruch auf bestimmte Funktionen oder auf deren unveränderten Fortbestand
        besteht nicht. Wir dürfen Funktionen weiterentwickeln, ändern oder einstellen, soweit Ihnen das zumutbar ist.
        Wesentliche Einschränkungen kündigen wir mit angemessener Frist per E-Mail an.
      </p>
      <p>
        (3) Die Angaben zu Veranstaltungen stammen überwiegend aus öffentlichen Quellen der Veranstalter und werden teils
        automatisch aufbereitet. Wir prüfen sie mit Sorgfalt, können aber nicht garantieren, dass Termine, Orte, Preise
        oder Beschreibungen vollständig, aktuell und richtig sind. Maßgeblich sind die Angaben des jeweiligen
        Veranstalters. Verträge über den Besuch einer Veranstaltung (z.&thinsp;B. Ticketkauf) kommen nicht mit uns
        zustande.
      </p>
      <p>
        (4) Wir bemühen uns um eine möglichst unterbrechungsfreie Erreichbarkeit, schulden aber keine bestimmte
        Verfügbarkeit. Wartungen, Störungen und Ausfälle bei Dienstleistern können die Nutzung zeitweise einschränken.
      </p>

      <h2>§ 3 Registrierung und Vertragsschluss</h2>
      <p>
        (1) Für ein Konto brauchen Sie eine gültige E-Mail-Adresse und ein Passwort. Mit dem Klick auf „Konto anlegen“
        geben Sie ein Angebot auf Abschluss eines Nutzungsvertrags zu diesen Bedingungen ab. Der Vertrag kommt zustande,
        wenn Sie Ihre E-Mail-Adresse über den Link in unserer Bestätigungsmail bestätigen.
      </p>
      <p>
        (2) Ein Konto dürfen nur Personen anlegen, die mindestens 16 Jahre alt sind. Mit dem entsprechenden Häkchen
        bestätigen Sie Ihr Alter. Nach der Bestätigung Ihrer E-Mail-Adresse geben Sie Ihren Vor- und Nachnamen und Ihr
        Geburtsdatum an; diese Angaben sind Pflicht und müssen zutreffen. Ergibt das Geburtsdatum ein Alter unter 16
        Jahren, sperren wir das Konto sofort und löschen es innerhalb von drei Tagen.
      </p>
      <p>(3) Jede Person darf nur ein Konto führen. Das Konto ist nicht übertragbar.</p>
      <p>
        (4) Sie sind verpflichtet, Ihr Passwort geheim zu halten und nicht für andere Dienste zu verwenden, die nicht
        Ihnen gehören. Besteht der Verdacht, dass Dritte Ihr Passwort kennen, ändern Sie es bitte sofort im Konto oder
        über „Passwort vergessen“ und informieren uns, wenn Ihr Konto missbraucht wurde.
      </p>

      <h2>§ 4 Pflichten und unzulässige Nutzung</h2>
      <p>Bei der Nutzung des Kontos ist insbesondere untersagt:</p>
      <ol className="rechtliches__liste">
        <li>
          automatisierte Zugriffe auf Konto-Funktionen (z.&thinsp;B. Skripte, Bots, massenhaftes Anlegen von Konten),
          soweit sie über die übliche Nutzung durch einen Browser oder unsere App hinausgehen;
        </li>
        <li>
          Versuche, Sicherheitsvorkehrungen zu umgehen, auf fremde Konten oder nicht für Sie bestimmte Daten zuzugreifen
          oder die Website in ihrer Funktion zu stören;
        </li>
        <li>das Anlegen von Konten mit fremden E-Mail-Adressen oder unter falscher Identität;</li>
        <li>jede Nutzung, die gegen geltendes Recht verstößt.</li>
      </ol>

      <h2>§ 5 Ihre Daten</h2>
      <p>
        (1) Wie wir Ihre personenbezogenen Daten verarbeiten, steht in unserer{" "}
        <Link href="/datenschutz#konto">Datenschutzerklärung</Link>. Einwilligungen (z.&thinsp;B. für persönliche
        Empfehlungen, die kontoübergreifende Speicherung bestimmter Merkungen oder Geburtstagsmails) sind freiwillig. Sie
        können sie jederzeit im Konto widerrufen, ohne dass die übrigen Funktionen des Kontos davon abhängen.
      </p>
      <p>(2) Sie können Ihre Daten jederzeit im Konto als Datei herunterladen.</p>

      <h2>§ 6 Laufzeit und Kündigung durch Sie</h2>
      <p>(1) Der Nutzungsvertrag läuft auf unbestimmte Zeit.</p>
      <p>
        (2) Sie können ihn jederzeit ohne Frist beenden, indem Sie Ihr Konto im Bereich „Konto“ löschen oder uns per
        E-Mail an <a href="mailto:moin@rocktician.com">moin@rocktician.com</a> darum bitten. Mit der Löschung entfernen wir
        Ihr Konto und die zugehörigen Daten nach Maßgabe der Datenschutzerklärung.
      </p>

      <h2>§ 7 Kündigung und Sperrung durch uns</h2>
      <p>
        (1) Wir können den Nutzungsvertrag mit einer Frist von zwei Wochen per E-Mail kündigen, etwa wenn wir die
        Konto-Funktion insgesamt einstellen.
      </p>
      <p>
        (2) Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt. Ein wichtiger Grund liegt
        insbesondere vor bei einem schwerwiegenden oder trotz Hinweis wiederholten Verstoß gegen § 3 Abs. 2 bis 4 oder
        § 4.
      </p>
      <p>
        (3) Bei einem begründeten Verdacht auf einen Verstoß nach § 4 Nr. 1 bis 3 dürfen wir das Konto vorübergehend
        sperren, um weiteren Schaden abzuwenden. Wir informieren Sie darüber per E-Mail, nennen den Grund, soweit dem
        keine Sicherheitsgründe entgegenstehen, und geben Ihnen Gelegenheit zur Stellungnahme.
      </p>
      <p>(4) Automatische Löschungen:</p>
      <ul>
        <li>Konten ohne Nutzung löschen wir nach 24 Monaten. Wir kündigen das einen Monat vorher per E-Mail an.</li>
        <li>
          Konten, deren E-Mail-Adresse nicht bestätigt wurde, löschen wir nach 48 Stunden. Weil der Löschlauf nur alle
          drei Tage stattfindet, geschieht das spätestens nach fünf Tagen.
        </li>
        <li>Konten ohne Altersbestätigung (§ 3 Abs. 2) löschen wir nach 7 Tagen, spätestens nach 10 Tagen.</li>
        <li>
          Konten, die wegen eines Alters unter 16 Jahren gesperrt sind (§ 3 Abs. 2), löschen wir innerhalb von drei
          Tagen.
        </li>
      </ul>
      <p>Einzelheiten stehen in der Datenschutzerklärung.</p>

      <h2>§ 8 Inhalte und Links Dritter</h2>
      <p>
        Veranstaltungsseiten verweisen auf Angebote Dritter, etwa auf Ticketverkäufer oder Websites der Veranstalter. Für
        deren Inhalte und Bedingungen sind ausschließlich die jeweiligen Anbieter verantwortlich.
      </p>

      <h2>§ 9 Haftung</h2>
      <p>
        (1) Wir haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit, bei der Verletzung von Leben, Körper oder
        Gesundheit, nach dem Produkthaftungsgesetz sowie im Umfang einer übernommenen Garantie.
      </p>
      <p>
        (2) Bei leichter Fahrlässigkeit haften wir nur für die Verletzung einer wesentlichen Vertragspflicht, deren
        Erfüllung die ordnungsgemäße Durchführung des Vertrags überhaupt erst ermöglicht und auf deren Einhaltung Sie
        regelmäßig vertrauen dürfen. In diesem Fall ist die Haftung auf den vertragstypischen, vorhersehbaren Schaden
        begrenzt.
      </p>
      <p>
        (3) Im Übrigen ist die Haftung ausgeschlossen. Das gilt auch für Schäden, die dadurch entstehen, dass Angaben zu
        Veranstaltungen unrichtig oder nicht aktuell sind (§ 2 Abs. 3), soweit nicht Abs. 1 greift.
      </p>
      <p>(4) Die Beschränkungen gelten auch zugunsten unserer Mitarbeitenden und Beauftragten.</p>

      <h2>§ 10 Änderungen dieser Bedingungen</h2>
      <p>
        (1) Wir können diese Bedingungen mit Wirkung für die Zukunft ändern, wenn dafür ein sachlicher Grund besteht,
        etwa geänderte Rechtslage, neue Funktionen oder Sicherheitsanforderungen, und Ihre berechtigten Interessen
        gewahrt bleiben.
      </p>
      <p>
        (2) Änderungen teilen wir Ihnen spätestens sechs Wochen vor ihrem Inkrafttreten per E-Mail mit. Sie können der
        Änderung bis zum Inkrafttreten widersprechen oder Ihr Konto jederzeit kostenlos löschen. Widersprechen Sie nicht
        und nutzen Ihr Konto nach dem Inkrafttreten weiter, gelten die geänderten Bedingungen. Auf diese Folge weisen wir
        in der Mitteilung gesondert hin. Im Fall eines Widerspruchs können beide Seiten den Vertrag nach § 6 bzw. § 7
        Abs. 1 beenden.
      </p>

      <h2 id="widerruf">§ 11 Widerrufsbelehrung</h2>
      <h3>Widerrufsrecht</h3>
      <p>
        Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen. Die
        Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses.
      </p>
      <p>
        Um Ihr Widerrufsrecht auszuüben, müssen Sie uns (Rocktician e.&thinsp;K., Inhaber Yannick Fetsch, Erkrather Str.
        401, 40231 Düsseldorf, E-Mail: <a href="mailto:moin@rocktician.com">moin@rocktician.com</a>) mittels einer
        eindeutigen Erklärung (z.&thinsp;B. eine E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen,
        informieren. Sie können dafür das beigefügte Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben
        ist. Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des Widerrufsrechts
        vor Ablauf der Widerrufsfrist absenden. Das Löschen Ihres Kontos im Bereich „Konto“ ist ebenfalls eine
        eindeutige Erklärung in diesem Sinne.
      </p>
      <h3>Folgen des Widerrufs</h3>
      <p>
        Wenn Sie diesen Vertrag widerrufen, löschen wir Ihr Konto und die zugehörigen Daten nach Maßgabe der
        Datenschutzerklärung. Da das Konto kostenlos ist, sind keine Zahlungen zu erstatten, und Sie schulden uns keinen
        Wertersatz.
      </p>
      <h3>Muster-Widerrufsformular</h3>
      <p>(Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular aus und senden Sie es zurück.)</p>
      <p className="rechtliches__kasten">
        – An Rocktician e.&thinsp;K., Erkrather Str. 401, 40231 Düsseldorf, E-Mail: moin@rocktician.com:
        <br />– Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über die Bereitstellung der
        folgenden digitalen Dienstleistung: Nutzerkonto auf diesdas.events
        <br />– Abgeschlossen am (*):
        <br />– Name des/der Verbraucher(s):
        <br />– E-Mail-Adresse des Kontos:
        <br />– Datum:
        <br />
        (*) Unzutreffendes streichen.
      </p>

      <h2>§ 12 Schlussbestimmungen</h2>
      <p>
        (1) Es gilt das Recht der Bundesrepublik Deutschland. Gegenüber Verbraucherinnen und Verbrauchern gilt diese
        Rechtswahl nur, soweit dadurch nicht der Schutz durch zwingende Bestimmungen des Rechts des Staates entzogen wird,
        in dem sie ihren gewöhnlichen Aufenthalt haben.
      </p>
      <p>
        (2) Sind Sie Kaufmann, juristische Person des öffentlichen Rechts oder öffentlich-rechtliches Sondervermögen, ist
        Gerichtsstand Düsseldorf.
      </p>
      <p>
        (3) Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer
        Verbraucherschlichtungsstelle teilzunehmen.
      </p>
      <p>
        (4) Sollten einzelne Bestimmungen unwirksam sein, bleibt der Vertrag im Übrigen wirksam. An die Stelle
        unwirksamer Bestimmungen treten die gesetzlichen Vorschriften.
      </p>

      <p style={{ marginTop: 48 }}>
        <Link href="/" className="link">
          ← Zurück zur Startseite
        </Link>
      </p>
    </div>
  );
}
