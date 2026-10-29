import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Datenschutzerklärung",
  description: "Datenschutzerklärung von dies.das.düsseldorf – Informationen zur Verarbeitung personenbezogener Daten.",
};

export default function DatenschutzSeite() {
  return (
    <div className="container sektion rechtliches">
      <h1 className="d">Datenschutzerklärung</h1>
      <p className="klein">Stand: Oktober 2026</p>

      <h2>1. Verantwortlicher</h2>
      <p>
        Rocktician e.&thinsp;K.
        <br />
        Inhaber: Yannick Fetsch
        <br />
        Erkrather Str. 401, 40231 Düsseldorf
        <br />
        E-Mail: <a href="mailto:moin@rocktician.com">moin@rocktician.com</a>
        <br />
        Telefon: <a href="tel:+4917657605826">+49 176 576 05 826</a>
      </p>

      <h2>2. Allgemeines zur Datenverarbeitung</h2>
      <p>
        Der Schutz Ihrer personenbezogenen Daten ist uns wichtig. Wir verarbeiten personenbezogene Daten
        unserer Nutzer grundsätzlich nur, soweit dies zur Bereitstellung einer funktionsfähigen Website sowie
        unserer Inhalte und Leistungen erforderlich ist. Die Verarbeitung erfolgt auf Grundlage der
        Datenschutz-Grundverordnung (DSGVO), des Bundesdatenschutzgesetzes (BDSG) und des
        Telekommunikation-Digitale-Dienste-Datenschutz-Gesetzes (TDDDG).
      </p>

      <h2>3. Hosting und Server-Logfiles</h2>
      <p>
        Diese Website wird bei einem externen Hosting-Anbieter gehostet. Bei jedem Zugriff werden automatisch
        folgende Daten in Server-Logfiles gespeichert:
      </p>
      <ul>
        <li>Besuchte Seite / abgerufene Datei</li>
        <li>Datum und Uhrzeit des Zugriffs</li>
        <li>Übertragene Datenmenge</li>
        <li>Browser-Typ und -Version</li>
        <li>Betriebssystem</li>
        <li>Referrer-URL (zuvor besuchte Seite)</li>
        <li>Anonymisierte IP-Adresse</li>
      </ul>
      <p>
        Diese Daten werden zur Sicherstellung des Betriebs, zur Fehlerbehebung und zur Missbrauchserkennung
        erhoben. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse). Die Logfiles werden
        nach 30 Tagen automatisch gelöscht.
      </p>

      <h2>4. SSL-Verschlüsselung</h2>
      <p>
        Diese Seite nutzt aus Sicherheitsgründen eine SSL-Verschlüsselung. Eine verschlüsselte Verbindung
        erkennen Sie an &quot;https://&quot; in der Adresszeile Ihres Browsers.
      </p>

      <h2>5. Cookies</h2>
      <p>
        Wir verwenden auf unserer Website folgende Arten von Cookies:
      </p>
      <ul>
        <li>
          <b>Technisch notwendige Cookies:</b> Diese Cookies sind für den Betrieb der Website erforderlich
          (z.&thinsp;B. Speicherung Ihrer Cookie-Einstellungen, Theme-Präferenz, Merkliste). Rechtsgrundlage
          ist Art. 6 Abs. 1 lit. f DSGVO.
        </li>
        <li>
          <b>Analyse-Cookies (Google Analytics):</b> Diese Cookies werden nur gesetzt, wenn Sie dem über
          unser Cookie-Banner ausdrücklich zugestimmt haben. Rechtsgrundlage ist Art. 6 Abs. 1 lit. a DSGVO
          (Einwilligung). Sie können Ihre Einwilligung jederzeit widerrufen, indem Sie Ihre Cookies löschen.
        </li>
      </ul>

      <h2>6. Google Analytics</h2>
      <p>
        Diese Website nutzt Google Analytics 4, einen Webanalysedienst der Google Ireland Limited
        (&quot;Google&quot;), Gordon House, Barrow Street, Dublin 4, Irland. Google Analytics wird
        <b> nur nach Ihrer ausdrücklichen Einwilligung</b> über unser Cookie-Banner aktiviert.
      </p>
      <p>
        Wir nutzen Google Analytics mit der Erweiterung zur Anonymisierung von IP-Adressen
        (<code>anonymize_ip</code>). Ihre IP-Adresse wird von Google innerhalb der EU gekürzt und nur in
        Ausnahmefällen vollständig an einen Server von Google in den USA übertragen und dort gekürzt.
      </p>
      <p>
        Google verarbeitet die Daten in unserem Auftrag, um die Nutzung der Website auszuwerten, Berichte über
        Website-Aktivitäten zusammenzustellen und weitere mit der Nutzung verbundene Dienstleistungen zu
        erbringen. Die von Google Analytics erhobenen Daten werden nicht mit anderen Google-Daten
        zusammengeführt.
      </p>
      <p>
        Rechtsgrundlage: Art. 6 Abs. 1 lit. a DSGVO (Einwilligung). Sie können Ihre Einwilligung jederzeit
        widerrufen, indem Sie die Cookies in Ihrem Browser löschen. Weitere Informationen finden Sie in der{" "}
        <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">
          Datenschutzerklärung von Google
        </a>
        .
      </p>

      <h2>7. Lokale Speicherung (localStorage)</h2>
      <p>
        Wir nutzen die lokale Speicherfunktion Ihres Browsers (localStorage) für folgende Zwecke:
      </p>
      <ul>
        <li>Speicherung Ihrer Merkliste (favorisierte Events)</li>
        <li>Speicherung Ihrer Theme-Einstellung (hell/dunkel)</li>
        <li>Speicherung Ihrer Cookie-Consent-Entscheidung</li>
      </ul>
      <p>
        Diese Daten werden ausschließlich lokal in Ihrem Browser gespeichert und nicht an uns oder Dritte
        übermittelt. Sie können diese Daten jederzeit über die Browser-Einstellungen löschen.
      </p>

      <h2>8. Externe Inhalte</h2>
      <p>
        Auf unseren Seiten können Inhalte Dritter eingebunden sein:
      </p>
      <ul>
        <li>
          <b>Google Fonts:</b> Schriftarten werden von Google-Servern geladen. Dabei wird Ihre IP-Adresse an
          Google übermittelt. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO.{" "}
          <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">
            Datenschutzerklärung von Google
          </a>
        </li>
        <li>
          <b>Google Maps:</b> Für Kartenansichten und Routenplanung werden Daten an Google übermittelt.
          Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO.
        </li>
        <li>
          <b>Event-Bilder:</b> Bilder können von externen Quellen (Veranstalter-Websites) stammen. Beim Laden
          dieser Bilder wird Ihre IP-Adresse an den jeweiligen Server übermittelt.
        </li>
      </ul>

      <h2>9. Kontaktaufnahme</h2>
      <p>
        Wenn Sie uns per E-Mail kontaktieren, werden Ihre Angaben einschließlich der von Ihnen angegebenen
        Kontaktdaten zwecks Bearbeitung der Anfrage und für den Fall von Anschlussfragen bei uns gespeichert.
        Diese Daten geben wir nicht ohne Ihre Einwilligung weiter. Rechtsgrundlage: Art. 6 Abs. 1 lit. b
        DSGVO (Vertragserfüllung / vorvertragliche Maßnahmen) bzw. Art. 6 Abs. 1 lit. f DSGVO (berechtigtes
        Interesse).
      </p>

      <h2>10. Ihre Rechte</h2>
      <p>Sie haben jederzeit das Recht auf:</p>
      <ul>
        <li><b>Auskunft</b> über Ihre bei uns gespeicherten personenbezogenen Daten (Art. 15 DSGVO)</li>
        <li><b>Berichtigung</b> unrichtiger Daten (Art. 16 DSGVO)</li>
        <li><b>Löschung</b> Ihrer Daten (Art. 17 DSGVO)</li>
        <li><b>Einschränkung</b> der Verarbeitung (Art. 18 DSGVO)</li>
        <li><b>Datenübertragbarkeit</b> (Art. 20 DSGVO)</li>
        <li><b>Widerspruch</b> gegen die Verarbeitung (Art. 21 DSGVO)</li>
        <li><b>Widerruf</b> einer erteilten Einwilligung (Art. 7 Abs. 3 DSGVO)</li>
      </ul>
      <p>
        Zur Ausübung Ihrer Rechte wenden Sie sich bitte an:{" "}
        <a href="mailto:moin@rocktician.com">moin@rocktician.com</a>
      </p>
      <p>
        Sie haben außerdem das Recht, sich bei einer Datenschutz-Aufsichtsbehörde über die Verarbeitung Ihrer
        personenbezogenen Daten zu beschweren.
      </p>

      <h2>11. Keine Weitergabe an Dritte</h2>
      <p>
        Eine Übermittlung Ihrer persönlichen Daten an Dritte zu anderen als den im Folgenden aufgeführten
        Zwecken findet nicht statt. Wir geben Ihre persönlichen Daten nur an Dritte weiter, wenn Sie Ihre
        ausdrückliche Einwilligung erteilt haben, die Weitergabe zur Geltendmachung von Rechtsansprüchen
        erforderlich ist oder eine gesetzliche Verpflichtung besteht.
      </p>

      <h2>12. Widerspruch gegen Werbe-Mails</h2>
      <p>
        Der Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten zur Übersendung von
        nicht ausdrücklich angeforderter Werbung und Informationsmaterialien wird hiermit widersprochen. Der
        Betreiber der Seiten behält sich ausdrücklich rechtliche Schritte im Falle der unverlangten Zusendung
        von Werbeinformationen vor.
      </p>

      <p style={{ marginTop: 48 }}>
        <Link href="/" className="link">
          ← Zurück zur Startseite
        </Link>
      </p>
    </div>
  );
}
