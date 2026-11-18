// Event-Beschreibung mit Absätzen und Listen (Texte aus Veranstalter-Quellen sind gegliedert)
import { beschreibungsBloecke, fettTeile } from "@/lib/beschreibung";

/** Zeile mit „**fett**“ als <strong>, sonst unverändert (nur wenn die Seite es einschaltet). */
function Zeile({ text, fett }: { text: string; fett: boolean }) {
  if (!fett) return <>{text}</>;
  return <>{fettTeile(text).map((t, i) => (t.fett ? <strong key={i}>{t.text}</strong> : <span key={i}>{t.text}</span>))}</>;
}

/** `fett`: „**Wort**“ fett darstellen – nur für eigene redaktionelle Texte (Weihnachtsmärkte), nicht für Quelltexte. */
export function BeschreibungText({ text, fett = false }: { text: string | null | undefined; fett?: boolean }) {
  const bloecke = beschreibungsBloecke(text);
  if (!bloecke.length) return null;
  return (
    <div className="beschreibung">
      {bloecke.map((b, i) =>
        b.art === "liste" ? (
          <ul key={i}>
            {b.punkte.map((p, j) => (
              <li key={j}><Zeile text={p} fett={fett} /></li>
            ))}
          </ul>
        ) : (
          <p key={i}>
            {b.zeilen.map((z, j) => (
              <span key={j}>
                {j > 0 && <br />}
                <Zeile text={z} fett={fett} />
              </span>
            ))}
          </p>
        ),
      )}
    </div>
  );
}
