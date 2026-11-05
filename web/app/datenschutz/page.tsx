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
        <li>
          Speicherung Ihrer Entscheidung, Google-Maps-Karten auf Event-Seiten dauerhaft anzuzeigen – nur wenn Sie
          „Karte anzeigen“ wählen; bei „Nur dieses Mal“ wird nichts gespeichert (siehe Abschnitt 9)
        </li>
      </ul>
      <p>
        Diese Daten werden ausschließlich lokal in Ihrem Browser gespeichert und nicht an uns oder Dritte
        übermittelt. Sie können diese Daten jederzeit über die Browser-Einstellungen löschen.
      </p>

      <h2>8. Social-Media-Auftritte</h2>
      <p>
        Wir betreiben Auftritte in den folgenden sozialen Netzwerken:
      </p>

      <h3>Instagram und Facebook (Meta)</h3>
      <p>
        Wir betreiben eine Instagram-Seite und ggf. eine Facebook-Seite innerhalb der Meta-Plattformen.
        Betreiber ist die Meta Platforms Ireland Limited, Merrion Road, Dublin 4, D04 X2K5, Irland. Wenn Sie
        unsere Social-Media-Seiten besuchen, erhebt Meta Ihre Daten gemäß der{" "}
        <a href="https://www.facebook.com/privacy/policy/" target="_blank" rel="noopener">
          Meta-Datenschutzrichtlinie
        </a>
        . Dazu gehören u.&thinsp;a. Ihre IP-Adresse, Browser-Informationen und Ihr Nutzungsverhalten.
      </p>
      <p>
        Wir nutzen die von Meta bereitgestellten Seitenstatistiken (Insights), um unser Angebot zu verbessern.
        Diese Statistiken werden uns ausschließlich in anonymisierter bzw. aggregierter Form bereitgestellt. Wir
        haben mit Meta eine Vereinbarung über die gemeinsame Verantwortlichkeit gemäß Art. 26 DSGVO
        geschlossen. Weitere Informationen finden Sie in der{" "}
        <a href="https://www.facebook.com/legal/terms/page_controller_addendum" target="_blank" rel="noopener">
          Seiten-Insights-Ergänzung von Meta
        </a>
        .
      </p>
      <p>
        Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an der Öffentlichkeitsarbeit und
        Kommunikation mit Nutzern). Daten können in die USA übertragen werden. Meta stützt die Übermittlung auf
        Standardvertragsklauseln gemäß Art. 46 Abs. 2 lit. c DSGVO.
      </p>

      <h3>Instagram Graph API (automatisches Posting)</h3>
      <p>
        Wir nutzen die Instagram Graph API, um automatisiert Inhalte auf unserem Instagram-Profil zu
        veröffentlichen. Dabei werden ausschließlich von uns erstellte Inhalte (Event-Posts, Bilder,
        Beschreibungen) an die Meta-Server übermittelt. Es werden keine personenbezogenen Daten unserer
        Website-Nutzer an die Instagram Graph API übertragen.
      </p>

      <h2>9. Externe Inhalte und Drittanbieter</h2>
      <p>
        Auf unseren Seiten können Inhalte Dritter eingebunden sein:
      </p>
      <ul>
        <li>
          <b>Schriftarten:</b> Alle Schriftarten dieser Website (einschließlich der Icon-Schrift) werden lokal
          von unserem eigenen Server ausgeliefert. Beim Seitenaufruf wird keine Verbindung zu Servern von
          Google oder anderen Schriftanbietern hergestellt.
        </li>
        <li>
          <b>Bilder und Karten in den Guides:</b> Event-Bilder der Veranstalter und Fotos von Restaurants und
          Cafés werden über unseren eigenen Server ausgeliefert; Ihr Browser verbindet sich dabei nicht mit den
          Servern der Veranstalter oder von Google. Die Kartenansicht der Guides nutzt Kartendaten von
          OpenStreetMap (© OpenStreetMap-Mitwirkende, ODbL), die ebenfalls vollständig auf unserem Server
          liegen – beim Anzeigen der Karte werden keine Daten an Kartendienste übermittelt. Erst wenn Sie auf die
          Quellenangabe „© OpenStreetMap-Mitwirkende“ klicken, öffnet sich die Website openstreetmap.org.
        </li>
        <li>
          <b>Google Maps (nur nach Klick):</b> Auf Event-Seiten können Sie einen Kartenausschnitt von Google Maps
          (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland) einblenden. Die Karte wird erst
          geladen, wenn Sie auf „Karte anzeigen“ oder „Nur dieses Mal“ klicken; erst dann werden Daten (u.a. Ihre
          IP-Adresse) an Google übermittelt, ggf. auch in die USA. Bei „Karte anzeigen“ speichern wir Ihre
          Entscheidung lokal in Ihrem Browser (siehe Abschnitt 7); Sie können sie dort jederzeit löschen. Links
          zur Routenplanung auf Event-Seiten und der Knopf „Google Maps“ auf den Seiten der Restaurant- und
          Café-Guides öffnen Google Maps erst, wenn Sie sie anklicken; dabei übermitteln wir nicht, von welcher
          unserer Seiten Sie kommen. Rechtsgrundlage: Ihre Einwilligung
          (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG).{" "}
          <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">
            Datenschutzerklärung von Google
          </a>
        </li>
        <li>
          <b>Supabase:</b> Wir nutzen Supabase als Datenbank-Backend für die Speicherung von Event-Daten.
          Supabase wird von Supabase, Inc., 970 Toa Payoh North #07-04, Singapore 318992 betrieben.
          Die Daten liegen auf Supabase-Servern (AWS, Region EU, Frankfurt). Neben Event-Daten speichern wir dort
          Newsletter-Anmeldungen (Abschnitt 11) sowie über „Event melden“ eingereichte Angaben und Bilder
          (Abschnitt 12). Ihr Browser verbindet sich dabei nicht direkt mit Supabase – die Formulare werden an
          unseren Server gesendet, der die Daten weiterleitet.{" "}
          <a href="https://supabase.com/privacy" target="_blank" rel="noopener">
            Datenschutzerklärung von Supabase
          </a>
        </li>
      </ul>

      <h2>10. KI-basierte Datenverarbeitung</h2>
      <p>
        Wir nutzen künstliche Intelligenz (Anthropic Claude API und OpenAI DALL-E) zur automatisierten
        Aufbereitung von Event-Daten. Dies umfasst die Kategorisierung von Events, die Erstellung von
        Beschreibungstexten und ggf. die Generierung von Vorschaubildern. Es werden dabei ausschließlich
        öffentlich verfügbare Event-Informationen verarbeitet, keine personenbezogenen Daten von Nutzern.
      </p>

      <h2 id="newsletter">11. Newsletter</h2>
      <p>
        Wenn Sie unseren Newsletter abonnieren, speichern wir Ihre E-Mail-Adresse und den Zeitpunkt der
        Anmeldung für den künftigen Versand (Supabase, siehe Abschnitt 9). Derzeit verschicken wir noch keine
        Newsletter. Bevor die erste Ausgabe verschickt wird, bitten wir Sie per E-Mail, Ihre Anmeldung zu
        bestätigen; ohne Bestätigung erhalten Sie keinen Newsletter. Rechtsgrundlage ist Art. 6 Abs. 1 lit. a
        DSGVO (Einwilligung). Sie können Ihre Anmeldung jederzeit per E-Mail an{" "}
        <a href="mailto:moin@rocktician.com">moin@rocktician.com</a> widerrufen – dann löschen wir Ihre
        E-Mail-Adresse unverzüglich. Sobald der Versand startet, enthält zusätzlich jede Ausgabe einen
        Abmeldelink.
      </p>

      <h2 id="event-melden">12. Event melden</h2>
      <p>
        Über das Formular „Event melden“ können Sie uns Veranstaltungen vorschlagen. Wir speichern dazu die
        Angaben zum Event, ein optional hochgeladenes Bild sowie Ihre Kontaktdaten (E-Mail-Adresse, optional
        Name) und eine eventuelle Anmerkung (Supabase, siehe Abschnitt 9). Die Kontaktdaten nutzen wir nur für
        Rückfragen zu Ihrer Meldung; sie werden nicht veröffentlicht. Veröffentlicht werden nach unserer
        Prüfung nur die Angaben zum Event und – wenn Sie die Rechte daran bestätigt haben – das Bild.
        Rechtsgrundlage ist Art. 6 Abs. 1 lit. a DSGVO (Einwilligung) bzw. lit. f (berechtigtes Interesse an
        einem vollständigen Veranstaltungskalender). Ein hochgeladenes Bild wird auf unserem Server neu
        gespeichert; dabei werden eingebettete Metadaten (z.B. Kameradaten, GPS-Position) entfernt. Die Meldung
        selbst – mit Kontaktdaten, Anmerkung und Original-Bild – löschen wir automatisch spätestens sechs Monate
        nach dem (letzten) Event-Tag, unabhängig davon, ob sie veröffentlicht oder abgelehnt wurde. Ein
        veröffentlichtes Event bleibt ohne Ihre Kontaktdaten in unserem Kalender. Eine frühere Löschung können
        Sie jederzeit per E-Mail an <a href="mailto:moin@rocktician.com">moin@rocktician.com</a> verlangen.
      </p>
      <p>
        Zum Schutz vor Missbrauch (Spam, automatisierte Massen-Einträge) verarbeitet unser Server bei beiden
        Formularen kurzzeitig Ihre IP-Adresse, um die Zahl der Anfragen zu begrenzen. Sie wird nur im
        Arbeitsspeicher gehalten (rund eine Stunde), nicht dauerhaft gespeichert und nicht weitergegeben
        (Art. 6 Abs. 1 lit. f DSGVO).
      </p>

      <h2>13. Kontaktaufnahme</h2>
      <p>
        Wenn Sie uns per E-Mail kontaktieren, werden Ihre Angaben einschließlich der von Ihnen angegebenen
        Kontaktdaten zwecks Bearbeitung der Anfrage und für den Fall von Anschlussfragen bei uns gespeichert.
        Diese Daten geben wir nicht ohne Ihre Einwilligung weiter. Rechtsgrundlage: Art. 6 Abs. 1 lit. b
        DSGVO (Vertragserfüllung / vorvertragliche Maßnahmen) bzw. Art. 6 Abs. 1 lit. f DSGVO (berechtigtes
        Interesse).
      </p>

      <h2>14. Ihre Rechte</h2>
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

      <h2>15. Keine Weitergabe an Dritte</h2>
      <p>
        Eine Übermittlung Ihrer persönlichen Daten an Dritte zu anderen als den im Folgenden aufgeführten
        Zwecken findet nicht statt. Wir geben Ihre persönlichen Daten nur an Dritte weiter, wenn Sie Ihre
        ausdrückliche Einwilligung erteilt haben, die Weitergabe zur Geltendmachung von Rechtsansprüchen
        erforderlich ist oder eine gesetzliche Verpflichtung besteht.
      </p>

      <h2>16. Widerspruch gegen Werbe-Mails</h2>
      <p>
        Der Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten zur Übersendung von
        nicht ausdrücklich angeforderter Werbung und Informationsmaterialien wird hiermit widersprochen. Der
        Betreiber der Seiten behält sich ausdrücklich rechtliche Schritte im Falle der unverlangten Zusendung
        von Werbeinformationen vor.
      </p>

      <h2>17. Aktualität und Änderung dieser Datenschutzerklärung</h2>
      <p>
        Diese Datenschutzerklärung ist aktuell gültig und hat den Stand Oktober 2026. Durch die
        Weiterentwicklung unserer Website oder aufgrund geänderter gesetzlicher bzw. behördlicher Vorgaben
        kann es notwendig werden, diese Datenschutzerklärung zu ändern. Die jeweils aktuelle Fassung kann
        jederzeit auf dieser Seite abgerufen werden.
      </p>

      <p style={{ marginTop: 48 }}>
        <Link href="/" className="link">
          ← Zurück zur Startseite
        </Link>
      </p>
    </div>
  );
}
