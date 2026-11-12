// Redaktionelle Texte der Guide-Seiten (lib/guide-texte.ts): Einleitung unter der Überschrift, längerer Text und
// fünf häufige Fragen am Seitenende. Alles serverseitig – steht in der ersten HTML-Antwort (SEO/GEO).
import Link from "next/link";
import { Fragment } from "react";
import { GUIDE_TEXTE, LINK_MUSTER, faqJsonLd, textFuellen, type GuideSeite } from "@/lib/guide-texte";
import { jsonLdText } from "@/lib/json-ld";

type Werte = Record<string, string>;

/** Text mit [Label](/pfad)-Links als React-Knoten (nur interne Pfade, siehe LINK_MUSTER). */
export function TextMitLinks({ text }: { text: string }) {
  const teile: React.ReactNode[] = [];
  let rest = 0;
  for (const m of text.matchAll(LINK_MUSTER)) {
    const start = m.index ?? 0;
    if (start > rest) teile.push(text.slice(rest, start));
    teile.push(<Link key={start} href={m[2]} className="gd-textlink">{m[1]}</Link>);
    rest = start + m[0].length;
  }
  if (rest < text.length) teile.push(text.slice(rest));
  return <>{teile.map((t, i) => <Fragment key={i}>{t}</Fragment>)}</>;
}

/** Kurze Einleitung (2–3 Sätze) direkt unter der Überschrift. */
export function GuideEinleitung({ seite, werte = {}, className = "gd-einleitung" }: { seite: GuideSeite; werte?: Werte; className?: string }) {
  return (
    <p className={className}>
      <TextMitLinks text={textFuellen(GUIDE_TEXTE[seite].einleitung, werte)} />
    </p>
  );
}

/** Längerer Text mit Zwischenüberschriften und die häufigen Fragen (mit FAQPage-JSON-LD). */
export function GuideSeoText({ seite, werte = {} }: { seite: GuideSeite; werte?: Werte }) {
  const t = GUIDE_TEXTE[seite];
  const faq = t.faq.map((f) => ({ frage: textFuellen(f.frage, werte), antwort: textFuellen(f.antwort, werte) }));
  return (
    <section className="container gd-seotext" aria-labelledby={`gd-seotext-${seite}`}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(faqJsonLd(faq)) }} />
      <h2 className="d" id={`gd-seotext-${seite}`}>{t.titel}</h2>
      {t.abschnitte.map((a) => (
        <div key={a.titel} className="gd-seotext__abschnitt">
          <h3>{a.titel}</h3>
          {a.absaetze.map((x, i) => (
            <p key={i}><TextMitLinks text={textFuellen(x, werte)} /></p>
          ))}
        </div>
      ))}
      <div className="gd-faq">
        <h2 className="d">Häufige Fragen</h2>
        {faq.map((f) => (
          <details key={f.frage} className="gd-faq__eintrag">
            <summary><span className="gd-faq__frage">{f.frage}</span><span className="icon" aria-hidden data-icon="expand_more" /></summary>
            <p><TextMitLinks text={f.antwort} /></p>
          </details>
        ))}
      </div>
    </section>
  );
}
