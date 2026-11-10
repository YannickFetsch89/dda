// Event-Beschreibung mit Absätzen und Listen (Texte aus Veranstalter-Quellen sind gegliedert)
import { beschreibungsBloecke } from "@/lib/beschreibung";

export function BeschreibungText({ text }: { text: string | null | undefined }) {
  const bloecke = beschreibungsBloecke(text);
  if (!bloecke.length) return null;
  return (
    <div className="beschreibung">
      {bloecke.map((b, i) =>
        b.art === "liste" ? (
          <ul key={i}>
            {b.punkte.map((p, j) => (
              <li key={j}>{p}</li>
            ))}
          </ul>
        ) : (
          <p key={i}>
            {b.zeilen.map((z, j) => (
              <span key={j}>
                {j > 0 && <br />}
                {z}
              </span>
            ))}
          </p>
        ),
      )}
    </div>
  );
}
