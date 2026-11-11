// /ueber – Über uns: emotional statt technisch. Bildstrecken (Partys, Konzerte, Drinks …) laufen beim Scrollen
// durchs Layout. Alle Fotos liegen in web/public/ueber/ – echte Fotos einfach mit GLEICHEM Dateinamen ablegen
// (Platzhalter sind JPGs im Format hoch 4:5, quer 8:5, quadratisch 1:1). Kein Client-JS: Laufbänder und Parallaxe
// sind reines CSS (animation-timeline: view() wo der Browser es kann, sonst stehen die Bilder einfach still).
import type { Metadata } from "next";
import Link from "next/link";
import { JsonLd } from "@/components/landing";
import { Icon } from "@/components/karten";
import { KONTAKT_MAIL } from "@/components/rahmen";
import { eventPoolLaden } from "@/lib/daten";
import { hubOrte } from "@/lib/guide-stadtteile";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { MARKE_SATZ, seitenMetadaten } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/ueber",
  titel: "Über uns – weil Düsseldorf zu gut ist, um drinnen zu hocken",
  beschreibung:
    "dies.das.düsseldorf ist dein persönlicher Kompass für Konzerte, Partys, Kultur und gutes Essen in Düsseldorf – gemacht von Menschen, die hier leben, lieben und ausgehen.",
  bild: "/ueber/party-1.jpg",
});

type Foto = { src: string; alt: string; format: "hoch" | "quer" | "quadrat" };

/** Bildliste – Reihenfolge bestimmt die Laufbänder. Echte Fotos: gleiche Dateinamen, Alt-Text hier anpassen. */
const F: Record<string, Foto> = {
  party: { src: "/ueber/party-1.jpg", alt: "Party mit tanzenden Menschen", format: "hoch" },
  konzert: { src: "/ueber/konzert-1.jpg", alt: "Konzert, Blick von der Menge auf die Bühne", format: "quer" },
  drink: { src: "/ueber/drink-1.jpg", alt: "Drink in Nahaufnahme", format: "hoch" },
  food: { src: "/ueber/food-1.jpg", alt: "Streetfood", format: "quadrat" },
  rhein: { src: "/ueber/rhein-1.jpg", alt: "Sommerabend am Rheinufer", format: "quer" },
  flohmarkt: { src: "/ueber/flohmarkt-1.jpg", alt: "Flohmarkt", format: "quadrat" },
  club: { src: "/ueber/club-1.jpg", alt: "DJ im Club", format: "hoch" },
  indie: { src: "/ueber/konzert-2.jpg", alt: "Kleines Indie-Konzert", format: "hoch" },
  cocktail: { src: "/ueber/drink-2.jpg", alt: "Cocktail in Nahaufnahme", format: "quadrat" },
  freunde: { src: "/ueber/freunde-1.jpg", alt: "Freunde unterwegs in Düsseldorf", format: "quer" },
  kultur: { src: "/ueber/kultur-1.jpg", alt: "Theater und Kunst", format: "hoch" },
  altstadt: { src: "/ueber/altstadt-1.jpg", alt: "Altstadt am Abend", format: "quer" },
};
const MASSE = { hoch: [1000, 1250], quer: [1600, 1000], quadrat: [1100, 1100] } as const;

function Bild({ f, className = "", eager = false }: { f: Foto; className?: string; eager?: boolean }) {
  const [w, h] = MASSE[f.format];
  return (
    // eslint-disable-next-line @next/next/no-img-element -- statische Fotos aus /public, Größen fest
    <img src={f.src} alt={f.alt} width={w} height={h} loading={eager ? "eager" : "lazy"} decoding="async" className={`ue-foto ue-foto--${f.format} ${className}`} />
  );
}

/** Endloses Laufband: die Liste steht zweimal hintereinander, die zweite Hälfte ist für Screenreader ausgeblendet. */
function Laufband({ fotos, richtung }: { fotos: Foto[]; richtung: "links" | "rechts" }) {
  return (
    <div className={`ue-band ue-band--${richtung}`}>
      <div className="ue-band__spur">
        {[...fotos, ...fotos].map((f, i) => (
          <div key={i} className="ue-band__bild" aria-hidden={i >= fotos.length || undefined}>
            <Bild f={i >= fotos.length ? { ...f, alt: "" } : f} />
          </div>
        ))}
      </div>
    </div>
  );
}

const zahl = (n: number) => n.toLocaleString("de-DE");

export default async function Ueber() {
  const [pool, restaurants, kneipen, clubs] = await Promise.all([eventPoolLaden(), hubOrte("restaurants-cafes"), hubOrte("kneipen-bars"), hubOrte("clubs")]);
  const echt = pool.quelle === "supabase";
  const krumen = [{ name: "Start", pfad: "/" }, { name: "Über uns", pfad: "/ueber" }];

  return (
    <div className="ue">
      <JsonLd daten={brotkrumenJsonLd(SITE_URL, krumen)} />

      {/* ── Hero: Schlagzeile und schwebende Collage ── */}
      <section className="ue-hero">
        <div className="container ue-hero__raster">
          <div className="ue-hero__text">
            <span className="overline overline--gold">Über uns</span>
            <h1 className="d">Weil Düsseldorf zu gut ist, um drinnen zu hocken</h1>
            <p className="ue-lead">
              Manchmal fragt man sich doch: Warum stolpert man eigentlich immer erst über das beste Konzert, den gemütlichsten Pop-up-Store oder den
              neuen Gastro-Geheimtipp, nachdem er schon vorbei ist?
            </p>
          </div>
          <div className="ue-collage" aria-hidden>
            <Bild f={F.party} className="ue-collage__a" eager />
            <Bild f={F.drink} className="ue-collage__b" eager />
            <Bild f={F.konzert} className="ue-collage__c" eager />
            <Bild f={F.food} className="ue-collage__d" />
          </div>
        </div>
      </section>

      <Laufband richtung="links" fotos={[F.konzert, F.cocktail, F.rhein, F.club, F.food, F.freunde, F.indie]} />

      {/* ── Wie es anfing ── */}
      <section className="container ue-abschnitt ue-anfang">
        <p className="ue-gross">
          Genau aus dieser leichten Frustration heraus ist <b>dies.das.düsseldorf</b> entstanden.
        </p>
        <div className="ue-anfang__spalten">
          <p>
            Wir sind kein seelenloser, algorithmusgesteuerter Ticketshop und kein grauer Veranstaltungskalender, durch den man sich quälen muss. Wir
            sind dein persönlicher Kompass für alles, was diese Stadt zu bieten hat – gemacht von Menschen, die genau wie du in Düsseldorf leben,
            lieben und ausgehen.
          </p>
          <Bild f={F.cocktail} className="ue-anfang__bild ue-parallaxe" />
        </div>
      </section>

      {/* ── Warum wir das machen: Text und versetztes Mosaik ── */}
      <section className="ue-warum">
        <div className="container ue-warum__raster">
          <div className="ue-warum__text">
            <h2 className="d">Warum wir das machen</h2>
            <p>
              Düsseldorf ist so viel mehr als die Königsallee und die längste Theke der Welt. Es ist das kreative Viertel in Flingern, das urbane
              Treiben im Medienhafen, der Falafel-Laden an der Ecke, der Open-Air-Flohmarkt am Rhein und das kleine Indie-Konzert im Hinterhof.
            </p>
            <p>
              Aber ganz ehrlich: Die Infos dazu waren oft verstreut auf tausend verschiedenen Instagram-Kanälen, alten Facebook-Gruppen oder schwer
              durchschaubaren Webseiten. Das wollten wir ändern. Wir bringen <i>dies</i> und <i>das</i> an einem Ort zusammen – übersichtlich,
              handverlesen und auf den Punkt.
            </p>
          </div>
          <div className="ue-mosaik" aria-hidden>
            <Bild f={F.flohmarkt} className="ue-mosaik__a ue-parallaxe" />
            <Bild f={F.indie} className="ue-mosaik__b ue-parallaxe ue-parallaxe--schnell" />
            <Bild f={F.rhein} className="ue-mosaik__c ue-parallaxe" />
          </div>
        </div>
      </section>

      {/* ── Philosophie: drei Karten ── */}
      <section className="container ue-abschnitt">
        <span className="overline overline--gold">Unsere Philosophie</span>
        <h2 className="d ue-h2">Was uns wichtig ist</h2>
        <div className="ue-karten">
          {[
            { nr: "01", titel: "Keine Masse, sondern Klasse", f: F.kultur, text: "Im Kalender findest du, was in der Stadt los ist – unsere Empfehlungen aber sind handverlesen. Wir kuratieren mit Liebe: Wenn wir dir etwas empfehlen, dann, weil wir es selbst großartig finden oder es unbedingt ausprobieren würden." },
            { nr: "02", titel: "Echt & nahbar", f: F.freunde, text: "Kein steriles Corporate-Blabla. Wir schreiben so, wie wir uns auch beim Bier in der Kneipe unterhalten würden: direkt, ehrlich und mit echtem lokalen Bezug." },
            { nr: "03", titel: "Für alle, die Düsseldorf neu entdecken wollen", f: F.altstadt, text: "Egal ob du seit 20 Jahren hier wohnst und dachtest, du kennst schon alles, oder ob du gerade erst hergezogen bist – bei uns findest du sowohl den Underground-Geheimtipp als auch den etablierten Klassiker." },
          ].map((k) => (
            <article key={k.nr} className="ue-karte">
              <div className="ue-karte__bild" aria-hidden>
                <Bild f={{ ...k.f, alt: "" }} />
              </div>
              <span className="ue-karte__nr d">{k.nr}</span>
              <h3 className="d">{k.titel}</h3>
              <p>{k.text}</p>
            </article>
          ))}
        </div>
      </section>

      <Laufband richtung="rechts" fotos={[F.party, F.drink, F.altstadt, F.kultur, F.flohmarkt, F.konzert, F.cocktail]} />

      {/* ── Wer dahintersteht: Polaroid-Stapel ── */}
      <section className="container ue-abschnitt ue-team">
        <div className="ue-polaroids" aria-hidden>
          <figure className="ue-polaroid ue-polaroid--1"><Bild f={F.freunde} /></figure>
          <figure className="ue-polaroid ue-polaroid--2"><Bild f={F.club} /></figure>
          <figure className="ue-polaroid ue-polaroid--3"><Bild f={F.food} /></figure>
        </div>
        <div>
          <h2 className="d ue-h2">Wer hinter den Kulissen steht</h2>
          <p>
            Hinter dies.das.düsseldorf steckt kein anonymer Medienkonzern, sondern ein kleines, enthusiastisches Team aus Düsseldorf-Fans. Uns
            verbindet die Begeisterung für gute Musik, gutes Essen, spannende Kultur und vor allem die Frage:
          </p>
          <p className="ue-frage d">„Sag mal, was machen wir eigentlich heute Abend?“</p>
          <p>
            Wir stecken unsere Köpfe in Event-Pläne, durchforsten Stadtteil-Blogs, sprechen mit Veranstaltern, Gastronomen und Machern aus der
            Nachbarschaft – damit du es auf einen Blick hast.
          </p>
        </div>
      </section>

      {/* ── Zahlen: was gerade drinsteckt (live) ── */}
      {echt && (
        <section className="ue-zahlen" aria-label="Gerade im Kalender">
          <div className="container">
            <p className="ue-zahlen__satz">{MARKE_SATZ}</p>
            <div className="ue-zahlen__raster">
              <div><b className="d">{zahl(pool.alle.length)}</b><span>Termine in den nächsten Wochen</span></div>
              <div><b className="d">{zahl(restaurants.length)}</b><span>Restaurants &amp; Cafés im Guide</span></div>
              <div><b className="d">{zahl(kneipen.length)}</b><span>Kneipen &amp; Bars</span></div>
              <div><b className="d">{zahl(clubs.length)}</b><span>Clubs</span></div>
            </div>
          </div>
        </section>
      )}

      {/* ── Mitmachen ── */}
      <section className="ue-cta">
        <div className="container ue-cta__raster">
          <div>
            <h2 className="d">Hast du einen Tipp oder ein Event für uns?</h2>
            <p>
              Düsseldorf lebt von seinen Menschen und seiner Community. Wenn du selbst ein Event planst, einen neuen Laden aufgemacht hast oder der
              Meinung bist, dass dein Lieblingsort unbedingt auf dies.das.düsseldorf auftauchen muss: Schreib uns!
            </p>
            <p>Lass uns gemeinsam dafür sorgen, dass niemand mehr etwas verpasst.</p>
            <div className="ue-cta__knoepfe">
              <Link href="/event-melden" className="btn btn--gold btn--gross">
                <Icon name="add_circle" /> Event melden
              </Link>
              <a href={`mailto:${KONTAKT_MAIL}?subject=Tipp für dies.das.düsseldorf`} className="btn btn--hell btn--gross">
                <Icon name="mail" /> Schreib uns
              </a>
              <a href="https://www.instagram.com/dies.das.duesseldorf/" target="_blank" rel="noopener" className="btn btn--hell btn--gross">
                Instagram
              </a>
            </div>
          </div>
          <Bild f={F.drink} className="ue-cta__bild ue-parallaxe" />
        </div>
      </section>

      <section className="container ue-gruss">
        <p className="d">Hab viel Spaß beim Entdecken,</p>
        <p className="d ue-gruss__name">Dein Team von dies.das.düsseldorf</p>
        <p className="ue-gruss__klein">
          Betrieben von Rocktician e.&thinsp;K. in Düsseldorf – alle Angaben im <Link href="/impressum">Impressum</Link>.
        </p>
      </section>
    </div>
  );
}
