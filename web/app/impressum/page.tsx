import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Impressum",
  description: "Impressum von dies.das.düsseldorf – Angaben gemäß § 5 DDG.",
};

export default function ImpressumSeite() {
  return (
    <div className="container sektion rechtliches">
      <h1 className="d">Impressum</h1>
      <p className="klein">Angaben gemäß § 5 DDG</p>

      <h2>Betreiber</h2>
      <p>
        Rocktician e.&thinsp;K.
        <br />
        Inhaber: Yannick Fetsch, B.Sc. Augenoptik/Optometrie
      </p>

      <h2>Anschrift</h2>
      <p>
        Rocktician Designstudio
        <br />
        Erkrather Str. 401
        <br />
        40231 Düsseldorf
      </p>
      <p>
        Unternehmenssitz lt. Handelsregister:
        <br />
        Gernotstraße 10
        <br />
        69502 Hemsbach, Deutschland
      </p>

      <h2>Kontakt</h2>
      <p>
        Mobil: <a href="tel:+4917657605826">+49 176 576 05 826</a>
        <br />
        E-Mail: <a href="mailto:moin@rocktician.com">moin@rocktician.com</a>
      </p>

      <h2>Handelsregister</h2>
      <p>
        HRA 707668, Amtsgericht Mannheim
      </p>

      <h2>Umsatzsteuer-ID</h2>
      <p>
        Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG:
        <br />
        DE301509854
      </p>

      <h2>Marke</h2>
      <p>
        Rocktician® ist eine eingetragene Marke (Nr. 30 2018 206 154) beim Deutschen Patent- und Markenamt.
      </p>

      <h2>Verantwortlich für den Inhalt gemäß § 55 Abs. 2 RStV</h2>
      <p>
        Yannick Fetsch
        <br />
        Erkrather Str. 401
        <br />
        40231 Düsseldorf
      </p>

      <h2>Haftung für Inhalte</h2>
      <p>
        Als Diensteanbieter sind wir gemäß § 7 Abs. 1 DDG für eigene Inhalte auf diesen Seiten nach den
        allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 DDG sind wir als Diensteanbieter jedoch nicht
        verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu
        forschen, die auf eine rechtswidrige Tätigkeit hinweisen. Verpflichtungen zur Entfernung oder Sperrung
        der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine
        diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung
        möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend
        entfernen.
      </p>

      <h2>Haftung für Links</h2>
      <p>
        Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben.
        Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der
        verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich. Die
        verlinkten Seiten wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße überprüft.
        Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar. Eine permanente inhaltliche
        Kontrolle der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht
        zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.
      </p>

      <h2>Urheberrecht</h2>
      <p>
        Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen
        Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der
        Grenzen des Urheberrechts bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers.
        Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet.
      </p>

      <p style={{ marginTop: 48 }}>
        <Link href="/" className="link">
          ← Zurück zur Startseite
        </Link>
      </p>
    </div>
  );
}
