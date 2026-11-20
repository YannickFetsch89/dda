// Datenschutzerklärung, Abschnitt „Nutzerkonto“ (Plan Nutzerkonten 9.4, Schritt 6). Wortlaut aus
// docs/datenschutz-konto-entwurf-2026-11-17.md, vom Anwalt freigegeben (Mitteilung des Auftraggebers vom 17.11.2026);
// die Änderungen zu E16 (Name und Geburtsdatum Pflicht) gehen zusätzlich in die schriftliche Freigabe.
// Sie-Form. Erscheint nur mit KONTEN_AKTIV (datenschutz/page.tsx).
import Link from "next/link";

const ZEILEN: [string, string, string, string][] = [
  [
    "Konto führen, Anmeldung",
    "E-Mail-Adresse, Passwort (nur als verschlüsselter Hash bei Supabase, nie im Klartext bei uns), Zeitpunkte von Anlage und Anmeldung, Sitzungen",
    "Art. 6 Abs. 1 lit. b DSGVO (Nutzungsvertrag)",
    "bis zur Löschung des Kontos; ohne Nutzung höchstens 24 Monate (siehe „Löschung“)",
  ],
  [
    "Name und Geburtsdatum (Pflichtangaben)",
    "Vorname, Nachname, Geburtsdatum",
    "Art. 6 Abs. 1 lit. b DSGVO (Nutzungsvertrag): Geburtsdatum zur Prüfung des Mindestalters von 16 Jahren, Name für Ticketkäufe über das Konto und für die persönliche Anrede auf der Website, in der App und in E-Mails",
    "bis zur Löschung des Kontos",
  ],
  ["Merkliste im Konto", "IDs der gemerkten Events, Zeitpunkt des Merkens", "Art. 6 Abs. 1 lit. b DSGVO", "wie das Konto"],
  [
    "Merkungen besonders schützenswerter Events",
    "IDs solcher Events, Zeitpunkt (siehe „Besonders schützenswerte Events“)",
    "Art. 9 Abs. 2 lit. a i. V. m. Art. 6 Abs. 1 lit. a DSGVO (ausdrückliche Einwilligung)",
    "bis zum Widerruf, spätestens mit dem Konto",
  ],
  [
    "Interessen und persönliche Vorschläge",
    "Ihre Angaben im Fragebogen (Kategorien, Stadtteile, Vorlieben) und die Auswertung Ihrer Merkliste für Vorschläge",
    "Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)",
    "bis zum Widerruf, dann sofort gelöscht; spätestens mit dem Konto",
  ],
  [
    "Anonyme Beliebtheits-Zählung",
    "Anzahl der Merkungen je Event, ohne Bezug zu einzelnen Personen im Ergebnis",
    "Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse), Widerspruch jederzeit möglich",
    "es werden keine Summen gespeichert; sie werden bei Bedarf aus den Merklisten gezählt",
  ],
  [
    "Geburtstagsmail",
    "Ihr Geburtsdatum aus dem Konto, Datum der letzten Geburtstagsmail",
    "Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG (Einwilligung)",
    "bis zum Widerruf (das Datum der letzten Mail wird dann gelöscht, das Geburtsdatum bleibt als Pflichtangabe im Konto); spätestens mit dem Konto",
  ],
  [
    "Altersbestätigung, Nutzungsbedingungen, Nachweis Ihrer Einwilligungen",
    "Zeitpunkt, Art der Erklärung, Fassung des angezeigten Textes",
    "Art. 6 Abs. 1 lit. b und c DSGVO, Art. 7 Abs. 1 DSGVO (Nachweispflicht)",
    "wie das Konto",
  ],
  [
    "Schutz vor Missbrauch",
    "IP-Adresse und eine verschlüsselte (gehashte) Form der E-Mail-Adresse, um Anmelde- und Registrierungsversuche zu begrenzen",
    "Art. 6 Abs. 1 lit. f DSGVO",
    "nur im Arbeitsspeicher, rund eine Stunde",
  ],
  [
    "Anmeldeprotokoll beim Dienstleister",
    "Nutzer-ID, E-Mail-Adresse, IP-Adresse, Zeitpunkt in den Protokollen von Supabase",
    "Art. 6 Abs. 1 lit. f DSGVO (Sicherheit des Dienstes)",
    "7 Tage",
  ],
];

export function KontoAbschnitt({ nr }: { nr: number }) {
  return (
    <>
      <h2 id="konto">{nr}. Nutzerkonto</h2>
      <p>
        Sie können die Website ohne Konto nutzen. Mit einem kostenlosen Nutzerkonto steht Ihre Merkliste auf mehreren
        Geräten zur Verfügung. Für das Konto brauchen wir Ihre E-Mail-Adresse, Ihren Vor- und Nachnamen und Ihr
        Geburtsdatum. Optional können Sie Interessen angeben und Geburtstagsmails erhalten. Für das Konto gelten
        zusätzlich unsere <Link href="/nutzungsbedingungen">Nutzungsbedingungen</Link>.
      </p>

      <h3>Welche Daten wir verarbeiten und wozu</h3>
      <div className="rechtliches__tabelle">
        <table>
          <thead>
            <tr>
              <th scope="col">Zweck</th>
              <th scope="col">Daten</th>
              <th scope="col">Rechtsgrundlage</th>
              <th scope="col">Speicherdauer</th>
            </tr>
          </thead>
          <tbody>
            {ZEILEN.map(([zweck, daten, grundlage, dauer]) => (
              <tr key={zweck}>
                <th scope="row">{zweck}</th>
                <td>{daten}</td>
                <td>{grundlage}</td>
                <td>{dauer}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p>
        <b>Registrierung und Mindestalter.</b> Ein Konto können Personen ab 16 Jahren anlegen. Das bestätigen Sie bei
        der Registrierung mit einem Häkchen. Nach der Registrierung schicken wir Ihnen eine E-Mail mit einem
        Bestätigungslink. Erst mit der Bestätigung ist das Konto nutzbar. Danach fragen wir Ihren Vor- und Nachnamen und
        Ihr Geburtsdatum ab. Ergibt sich aus dem Geburtsdatum ein Alter unter 16 Jahren, speichern wir weder Namen noch
        Datum, sperren das Konto sofort und löschen es innerhalb von drei Tagen.
      </p>
      <p>
        <b>Interessen und persönliche Vorschläge.</b> Nach der Bestätigung können Sie in einem kurzen Fragebogen
        Interessen angeben oder ihn überspringen. Ihre Antworten bleiben zunächst nur in Ihrem Browser. Gespeichert
        werden sie erst, wenn Sie am Ende ausdrücklich einwilligen. Sie können die Einwilligung jederzeit im Konto
        widerrufen. Dann löschen wir Ihre Antworten sofort.
      </p>

      <p>
        <b>Besonders schützenswerte Events.</b> Aus der Merkung mancher Events lassen sich Rückschlüsse auf sehr
        persönliche Dinge ziehen: Gesundheit, Religion oder Weltanschauung, sexuelle Orientierung oder geschlechtliche
        Identität, politische Meinung, Gewerkschaftszugehörigkeit oder ethnische Herkunft (Art. 9 DSGVO).
      </p>
      <ul>
        <li>
          Solche Events erkennen wir automatisch anhand von Stichwörtern in Titel, Ort und Beschreibung. Die
          Kennzeichnung betrifft nur das Event, nicht Sie.
        </li>
        <li>
          Ohne Ihre ausdrückliche Einwilligung speichern wir Merkungen solcher Events <b>nicht in Ihrem Konto</b>,
          sondern nur in Ihrem Browser auf dem Gerät, auf dem Sie sie gemerkt haben.
        </li>
        <li>Mit Einwilligung speichern wir sie in Ihrem Konto, damit sie auf allen Ihren Geräten verfügbar sind.</li>
        <li>
          Für persönliche Vorschläge und für die Beliebtheits-Zählung nutzen wir sie <b>nie</b>, auch nicht mit
          Einwilligung.
        </li>
        <li>
          Sie können die Einwilligung jederzeit im Konto widerrufen. Dann entfernen wir diese Merkungen aus Ihrem Konto.
          Auf dem Gerät, auf dem Sie widerrufen, bleiben sie gemerkt, auf Ihren anderen Geräten verschwinden sie.
        </li>
        <li>
          Wird ein Event erst nachträglich als besonders schützenswert erkannt, entfernen wir seine Merkung aus Konten
          ohne diese Einwilligung.
        </li>
      </ul>

      <p>
        <b>Anonyme Beliebtheits-Zählung und Ihr Widerspruchsrecht.</b> Wir zählen, wie oft Events gemerkt werden, um zu
        sehen, was in Düsseldorf beliebt ist, und unser Programm danach auszurichten. Dabei sehen wir nur Summen je
        Event, nie, wer was gemerkt hat. Besonders schützenswerte Events zählen nie mit. Grundlage ist unser
        berechtigtes Interesse (Art. 6 Abs. 1 lit. f DSGVO). Gezählt werden Konten erst, nachdem Sie diesen Hinweis bei
        der Einrichtung des Kontos gesehen haben.
      </p>
      <p className="rechtliches__kasten">
        <b>Ihr Widerspruchsrecht (Art. 21 DSGVO):</b> Sie können der Zählung jederzeit widersprechen, mit einem Häkchen
        bei der Einrichtung des Kontos oder später in Ihrem Konto. Ihre Merkliste zählt dann nicht mehr mit.
      </p>

      <p>
        <b>Geburtstagsmail.</b> Freiwillig können Sie einwilligen, dass wir Ihnen zum Geburtstag eine E-Mail mit
        Glückwünschen und Event-Tipps schicken. Dafür nutzen wir das Geburtsdatum aus Ihrem Konto. Sie können die
        Einwilligung jederzeit im Konto oder über den Abmeldelink in jeder Geburtstagsmail widerrufen. Das Geburtsdatum
        bleibt dann als Pflichtangabe im Konto gespeichert, wird aber nicht mehr für Mails genutzt.
      </p>
      <p>
        <b>E-Mails zum Konto.</b> Wir senden Ihnen E-Mails, die für das Konto nötig sind: Bestätigung der Adresse, Link
        zum Zurücksetzen des Passworts, gegebenenfalls einen Bestätigungscode und einen Hinweis vor der Löschung eines
        ungenutzten Kontos. Sie werden von Supabase ausgelöst und über den Mailserver unseres Hosting-Anbieters
        versendet (Abschnitt 3). Die E-Mails enthalten keine Zählpixel und keine Klick-Verfolgung.
      </p>

      <p>
        <b>Löschung.</b>
      </p>
      <ul>
        <li>
          Sie können Ihr Konto jederzeit selbst im Bereich „Konto“ löschen. Dabei löschen wir Ihre Merkliste, Ihre
          Angaben und die Nachweise Ihrer Einwilligungen.
        </li>
        <li>
          Konten, deren E-Mail-Adresse nicht bestätigt wurde, löschen wir nach 48 Stunden. Weil der Löschlauf alle drei
          Tage stattfindet, geschieht das spätestens nach fünf Tagen.
        </li>
        <li>Bestätigte Konten ohne Altersbestätigung löschen wir nach 7 Tagen, spätestens nach 10 Tagen.</li>
        <li>Konten, die wegen eines Alters unter 16 Jahren gesperrt sind, löschen wir innerhalb von drei Tagen.</li>
        <li>
          Konten, die 24 Monate lang nicht genutzt wurden, löschen wir. Als Nutzung zählt jede Anmeldung und jede Aktion
          im Konto, zum Beispiel das Merken eines Events. Wurde ein Konto nie genutzt, zählt die Frist ab der Anlage.
          Einen Monat vor der Löschung erhalten Sie eine E-Mail.
        </li>
        <li>
          Gelöschte Daten können noch bis zu 7 Tage in den Datensicherungen unseres Dienstleisters Supabase enthalten
          sein und werden dort danach überschrieben. Eine Wiederherstellung aus einer Sicherung führt nicht dazu, dass
          ein gelöschtes Konto wieder nutzbar wird.
        </li>
      </ul>

      <p>
        <b>Ihre Daten herunterladen.</b> Im Konto können Sie Ihre Kontodaten, Interessen, Einwilligungen und Ihre
        Merkliste als Datei herunterladen (Art. 20 DSGVO). Der Download ersetzt nicht Ihr Recht auf Auskunft nach Art. 15
        DSGVO. Eine vollständige Auskunft erhalten Sie per E-Mail an{" "}
        <a href="mailto:hallo@diesdas.events">hallo@diesdas.events</a>.
      </p>
      <p>
        <b>Empfänger und Drittland.</b> Die Kontodaten speichern wir bei Supabase (Abschnitt 9) in der EU (AWS,
        Frankfurt). Ein Zugriff durch Supabase, Inc. oder deren Unterauftragsverarbeiter aus Drittländern ist nicht
        ausgeschlossen. Grundlage dafür sind die Standardvertragsklauseln der EU-Kommission (Art. 46 Abs. 2 lit. c
        DSGVO). Mit Supabase und unserem Hosting-Anbieter bestehen Verträge zur Auftragsverarbeitung (Art. 28 DSGVO).
      </p>
    </>
  );
}
