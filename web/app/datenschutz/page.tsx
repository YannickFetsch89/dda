import type { Metadata } from "next";
import Link from "next/link";
import { kontenAktiv } from "@/lib/konto/konfig";
import { KontoAbschnitt } from "./konto-abschnitt";
import { PartnerLinksDatenschutz } from "@/components/partner-links";

/**
 * Stand mit Nutzerkonten (Plan Nutzerkonten Schritt 8): auf den Monat setzen, in dem KONTEN_AKTIV eingeschaltet wird.
 * Ohne Schalter gilt weiter der bisherige Stand.
 */
const STAND_MIT_KONTEN = "November 2026";
const STAND_OHNE_KONTEN = "Oktober 2026";

export const metadata: Metadata = {
  title: "Datenschutzerklärung",
  description: "Datenschutzerklärung von dies.das.düsseldorf – Informationen zur Verarbeitung personenbezogener Daten.",
};

export default function DatenschutzSeite() {
  // Mit Konten kommt Abschnitt 13 „Nutzerkonto“ dazu, die bisherigen Abschnitte 13–17 werden zu 14–18
  const konten = kontenAktiv();
  const nr = (alt: number) => (konten && alt >= 13 ? alt + 1 : alt);
  const stand = konten ? STAND_MIT_KONTEN : STAND_OHNE_KONTEN;
  return (
    <div className="container sektion rechtliches">
      <h1 className="d">Datenschutzerklärung</h1>
      <p className="klein">Stand: {stand}</p>

      <h2>1. Verantwortlicher</h2>
      <p>
        Rocktician e.&thinsp;K.
        <br />
        Inhaber: Yannick Fetsch
        <br />
        Erkrather Str. 401, 40231 Düsseldorf
        <br />
        E-Mail: <a href="mailto:hallo@diesdas.events">hallo@diesdas.events</a>
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
      {/* Newsletter-Double-Opt-in (Plan Admin-Dashboard 4.9, vom Anwalt freigegeben 23.11.2026): Satz gilt immer */}
      <p>
        Über den Mailserver unseres Hosting-Anbieters versenden wir außerdem{" "}
        {konten ? "die E-Mails zum Nutzerkonto (Abschnitt 13) und " : ""}die E-Mails zum Newsletter (Abschnitt 11)
        sowie die Mitteilung, dass ein von Ihnen gemeldetes Event veröffentlicht ist (Abschnitt 12). Dabei verarbeitet der Anbieter Ihre E-Mail-Adresse und den Inhalt der jeweiligen E-Mail in unserem Auftrag.
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
          {konten && (
            <>
              {" "}Wenn Sie sich in Ihrem Nutzerkonto anmelden, setzen wir zwei weitere technisch notwendige Cookies:
              <ul>
                <li>
                  <b>ddd_sitzung</b> enthält die Anmeldedaten Ihrer Sitzung. Es ist für Skripte auf der Seite nicht
                  lesbar (HttpOnly) und wird nur an die Konto-Funktionen unseres Servers geschickt, nicht bei normalen
                  Seitenaufrufen. Laufzeit: 30 Tage, verlängert bei Nutzung. Nach einem Klick auf „Passwort vergessen“
                  gilt es nur eine Stunde.
                </li>
                <li>
                  <b>ddd_konto</b> enthält nur „0“ oder „1“ und sagt der Seite, ob Sie angemeldet sind. So zeigt die
                  Seite Ihre Merkliste im richtigen Zustand an, ohne Ihre Anmeldedaten bei jedem Seitenaufruf
                  mitzuschicken. Laufzeit wie die Sitzung, gelöscht beim Abmelden.
                </li>
              </ul>
              Beide Cookies sind unbedingt erforderlich, damit eine von Ihnen gewünschte Anmeldung über mehrere Seiten
              hinweg bestehen bleibt (§ 25 Abs. 2 Nr. 2 TDDDG). Sie werden nur gesetzt, wenn Sie sich anmelden.
            </>
          )}
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
        {konten && (
          <>
            <li>
              wenn Sie angemeldet sind: eine Kopie Ihrer Konto-Merkliste und noch nicht übertragene Änderungen, damit die
              Merkliste auch bei schlechter Verbindung sofort reagiert
            </li>
            <li>
              Merkungen, die nur auf diesem Gerät gespeichert werden dürfen (Abschnitt 13, „Besonders schützenswerte
              Events“)
            </li>
            <li>ein Merker, dass Sie den Hinweis auf das Nutzerkonto nach dem ersten Merken schon gesehen haben</li>
          </>
        )}
      </ul>
      {konten ? (
        <p>
          Ohne Nutzerkonto werden diese Daten ausschließlich lokal in Ihrem Browser gespeichert und nicht an uns oder
          Dritte übermittelt. Wenn Sie angemeldet sind, wird Ihre Merkliste in Ihrem Konto gespeichert (Abschnitt 13).
          Auf dem Gerät liegt dann nur eine Kopie, die beim Abmelden gelöscht wird. Beim ersten Anmelden übernehmen wir
          die bisher nur auf dem Gerät gespeicherte Merkliste in Ihr Konto, wenn Ihr Konto noch keine Merkliste hatte;
          sonst fragen wir vorher nach. Sie können die lokal gespeicherten Daten jederzeit über die
          Browser-Einstellungen löschen.
        </p>
      ) : (
        <p>
          Diese Daten werden ausschließlich lokal in Ihrem Browser gespeichert und nicht an uns oder Dritte
          übermittelt. Sie können diese Daten jederzeit über die Browser-Einstellungen löschen.
        </p>
      )}

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
          <b>Google Maps (nur nach Klick):</b> Auf Event-Seiten und den Seiten des Spielplatz- und des Weihnachtsmarkt-Guides können Sie einen
          Kartenausschnitt von Google Maps
          (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland) einblenden. Die Karte wird erst
          geladen, wenn Sie auf „Karte anzeigen“ oder „Nur dieses Mal“ klicken; erst dann werden Daten (u.a. Ihre
          IP-Adresse) an Google übermittelt, ggf. auch in die USA. Bei „Karte anzeigen“ speichern wir Ihre
          Entscheidung lokal in Ihrem Browser (siehe Abschnitt 7); Sie können sie dort jederzeit löschen. Links
          zur Routenplanung auf Event-Seiten und der Knopf „Google Maps“ auf den Seiten der Restaurant- und
          Café-Guides und der Knopf „Route planen“ im Spielplatz- und im Weihnachtsmarkt-Guide öffnen Google Maps erst, wenn Sie sie anklicken; dabei übermitteln wir nicht, von welcher
          unserer Seiten Sie kommen. Rechtsgrundlage: Ihre Einwilligung
          (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG).{" "}
          <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">
            Datenschutzerklärung von Google
          </a>
        </li>
        <li>
          <b>Standortfunktion im Spielplatz-Guide.</b> Wenn Sie auf der Übersichtsseite des Spielplatz-Guides bei der
          Sortierung auf „In der Nähe“ tippen, fragt Ihr Browser, ob die Website Ihren Standort verwenden darf. Nur wenn
          Sie zustimmen, berechnet Ihr Browser auf Ihrem Gerät die Entfernung zu den Spielplätzen. Die Website erhält
          Ihren Standort dabei nicht und speichert ihn nicht. Die Freigabe können Sie jederzeit in den Einstellungen
          Ihres Browsers widerrufen. Der Link „In der Nähe“ auf einer Spielplatz-Seite springt nur zu den schon geladenen
          Angaben weiter unten und fragt den Standort nicht ab.
        </li>
        {/* Partner-Links (Plan Quellen-Ausbau 5.5.5, P2): nur, wenn ein Partnerprogramm aktiv ist */}
        <PartnerLinksDatenschutz />
        <li>
          <b>Supabase:</b> Wir nutzen Supabase als Datenbank-Backend für die Speicherung von Event-Daten.
          Supabase wird von Supabase, Inc., 970 Toa Payoh North #07-04, Singapore 318992 betrieben.
          Die Daten liegen auf Supabase-Servern (AWS, Region EU, Frankfurt). Neben Event-Daten speichern wir dort
          Newsletter-Anmeldungen (Abschnitt 11){konten ? "," : " sowie"} über „Event melden“ eingereichte Angaben und Bilder
          (Abschnitt 12)
          {konten && " sowie Nutzerkonten und Merklisten (Abschnitt 13). Supabase stellt außerdem die Anmeldung für Nutzerkonten bereit"}
          . Ihr Browser verbindet sich dabei nicht direkt mit Supabase – die Formulare werden an
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
      {/* Text vom Anwalt freigegeben 23.11.2026 (docs/anwalt-newsletter-doi-2026-11-23.md) */}
      <p>
        Wenn Sie unseren Newsletter abonnieren, speichern wir Ihre E-Mail-Adresse und den Zeitpunkt der
        Anmeldung (Supabase, siehe Abschnitt 9). Anschließend schicken wir Ihnen eine E-Mail mit einem
        Bestätigungslink (Double-Opt-in). Erst wenn Sie den Link aufrufen und die Anmeldung bestätigen, erhalten
        Sie den Newsletter; wir speichern dann zusätzlich den Zeitpunkt der Bestätigung als Nachweis Ihrer
        Einwilligung. Bestätigen Sie die Anmeldung nicht, löschen wir Ihre E-Mail-Adresse 30 Tage nach der
        Bestätigungs-E-Mail. Die E-Mails versenden wir über den Mailserver unseres Hosting-Anbieters, der dabei
        Ihre E-Mail-Adresse und den Inhalt der E-Mail in unserem Auftrag verarbeitet.
      </p>
      <p>
        Rechtsgrundlage ist Art. 6 Abs. 1 lit. a DSGVO (Einwilligung). Sie können Ihre Einwilligung jederzeit
        widerrufen – über den Abmeldelink in jeder E-Mail oder per E-Mail an{" "}
        <a href="mailto:hallo@diesdas.events">hallo@diesdas.events</a>. Mit der Abmeldung löschen wir Ihre
        E-Mail-Adresse sofort.
      </p>

      <h2 id="event-melden">12. Event melden</h2>
      <p>
        Über das Formular „Event melden“ können Sie uns Veranstaltungen vorschlagen. Wir speichern dazu die
        Angaben zum Event, ein optional hochgeladenes Bild sowie Ihre Kontaktdaten (E-Mail-Adresse, optional
        Name) und eine eventuelle Anmerkung (Supabase, siehe Abschnitt 9). Die Kontaktdaten nutzen wir für
        Rückfragen zu Ihrer Meldung und für eine einmalige E-Mail, sobald das Event veröffentlicht ist und noch
        bevorsteht (mit dem Link zum Event und einem Hinweis auf unser kostenloses Nutzerkonto); sie werden nicht veröffentlicht. Diese E-Mail
        versenden wir über den Mailserver unseres Hosting-Anbieters (Abschnitt 3). Veröffentlicht werden nach unserer
        Prüfung nur die Angaben zum Event und – wenn Sie die Rechte daran bestätigt haben – das Bild.
        Rechtsgrundlage ist Art. 6 Abs. 1 lit. a DSGVO (Einwilligung) bzw. lit. f (berechtigtes Interesse an
        einem vollständigen Veranstaltungskalender). Ein hochgeladenes Bild wird auf unserem Server neu
        gespeichert; dabei werden eingebettete Metadaten (z.B. Kameradaten, GPS-Position) entfernt. Die Meldung
        selbst – mit Kontaktdaten, Anmerkung und Original-Bild – löschen wir automatisch sechs Monate nach dem
        (letzten) Event-Tag (die Löschung läuft alle paar Tage), unabhängig davon, ob sie veröffentlicht oder
        abgelehnt wurde. Ein
        veröffentlichtes Event bleibt ohne Ihre Kontaktdaten in unserem Kalender. Eine frühere Löschung können
        Sie jederzeit per E-Mail an <a href="mailto:hallo@diesdas.events">hallo@diesdas.events</a> verlangen.
      </p>
      <p>
        Zum Schutz vor Missbrauch (Spam, automatisierte Massen-Einträge) verarbeitet unser Server bei beiden
        Formularen kurzzeitig Ihre IP-Adresse, um die Zahl der Anfragen zu begrenzen. Sie wird nur im
        Arbeitsspeicher gehalten (rund eine Stunde), nicht dauerhaft gespeichert und nicht weitergegeben
        (Art. 6 Abs. 1 lit. f DSGVO).
      </p>

      {konten && <KontoAbschnitt nr={13} />}

      <h2>{nr(13)}. Kontaktaufnahme</h2>
      <p>
        Wenn Sie uns per E-Mail kontaktieren, werden Ihre Angaben einschließlich der von Ihnen angegebenen
        Kontaktdaten zwecks Bearbeitung der Anfrage und für den Fall von Anschlussfragen bei uns gespeichert.
        Diese Daten geben wir nicht ohne Ihre Einwilligung weiter. Rechtsgrundlage: Art. 6 Abs. 1 lit. b
        DSGVO (Vertragserfüllung / vorvertragliche Maßnahmen) bzw. Art. 6 Abs. 1 lit. f DSGVO (berechtigtes
        Interesse).
      </p>

      <h2>{nr(14)}. Ihre Rechte</h2>
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
        <a href="mailto:hallo@diesdas.events">hallo@diesdas.events</a>
      </p>
      {konten && (
        <p>
          Wenn Sie ein Nutzerkonto haben, können Sie viele dieser Rechte direkt im Konto ausüben: Einwilligungen
          widerrufen, der Beliebtheits-Zählung widersprechen, Ihre Daten herunterladen und Ihr Konto löschen.
        </p>
      )}
      <p>
        Sie haben außerdem das Recht, sich bei einer Datenschutz-Aufsichtsbehörde über die Verarbeitung Ihrer
        personenbezogenen Daten zu beschweren.
      </p>

      <h2>{nr(15)}. Keine Weitergabe an Dritte</h2>
      <p>
        Eine Übermittlung Ihrer persönlichen Daten an Dritte zu anderen als den im Folgenden aufgeführten
        Zwecken findet nicht statt. Wir geben Ihre persönlichen Daten nur an Dritte weiter, wenn Sie Ihre
        ausdrückliche Einwilligung erteilt haben, die Weitergabe zur Geltendmachung von Rechtsansprüchen
        erforderlich ist oder eine gesetzliche Verpflichtung besteht.
        {konten &&
          " Keine Weitergabe in diesem Sinne ist die Verarbeitung durch Dienstleister, die Daten in unserem Auftrag und nach unseren Weisungen verarbeiten (Auftragsverarbeiter nach Art. 28 DSGVO), insbesondere unser Hosting-Anbieter (einschließlich E-Mail-Versand) und Supabase."}
      </p>

      <h2>{nr(16)}. Widerspruch gegen Werbe-Mails</h2>
      <p>
        Der Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten zur Übersendung von
        nicht ausdrücklich angeforderter Werbung und Informationsmaterialien wird hiermit widersprochen. Der
        Betreiber der Seiten behält sich ausdrücklich rechtliche Schritte im Falle der unverlangten Zusendung
        von Werbeinformationen vor.
      </p>

      <h2>{nr(17)}. Aktualität und Änderung dieser Datenschutzerklärung</h2>
      <p>
        Diese Datenschutzerklärung ist aktuell gültig und hat den Stand {stand}. Durch die
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
